"""Orchestrator Command Center Textual TUI.

ADDENDUM_01 §1 의 레이아웃:
  ┌──────────────┬───────────────┬───────────────┐
  │ Orch CLI Log │ Worker Slot 1 │ Worker Slot 2 │
  ├──────────────┼───────────────┼───────────────┤
  │ Dashboard    │ Worker Slot 3 │ Worker Slot 4 │
  └──────────────┴───────────────┴───────────────┘

오른쪽 Worker Slot 영역은 worker_slot_count 에 따라 자동 분할됩니다.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, RichLog, Static

from orchestrator import __version__
from orchestrator.config import AppConfig
from orchestrator.dashboard import DashboardSnapshot
from orchestrator.errors import ManifestError
from orchestrator.gate_view import gate_view
from orchestrator.pipeline import advance, next_action
from orchestrator.project_manager import approve_gate, load_manifest, reject_gate
from orchestrator.state_machine import GATES
from orchestrator.worker_slot_manager import WorkerSlotManager
from schemas.models import ProjectState, WorkerSlot, WorkerSlotsSnapshot


STATUS_STYLES = {
    "idle": "dim",
    "assigned": "yellow",
    "running": "bold green",
    "completed": "bold cyan",
    "failed": "bold red",
    "waiting_user": "bold magenta",
    "stale": "bold red on yellow",
}


class OrchLogPanel(RichLog):
    """왼쪽 상단 Orch CLI Log Panel."""

    DEFAULT_CSS = """
    OrchLogPanel {
        border: round $accent;
        height: 1fr;
    }
    """

    def __init__(self) -> None:
        super().__init__(highlight=False, markup=True, wrap=True, max_lines=500)
        self.border_title = "Orch CLI Log"


class DashboardPanel(Static):
    """왼쪽 하단 Job Dashboard."""

    DEFAULT_CSS = """
    DashboardPanel {
        border: round $primary;
        padding: 1 2;
        height: 1fr;
    }
    """

    snapshot: reactive[DashboardSnapshot | None] = reactive(None)

    def __init__(self) -> None:
        super().__init__("")
        self.border_title = "Job Dashboard"

    def watch_snapshot(self, snap: DashboardSnapshot | None) -> None:
        if snap is None:
            self.update("(no project loaded)")
            return
        gate = snap.current_gate or "-"
        next_action = snap.next_action or "-"
        text = (
            f"[bold]project[/bold] {snap.project_id}    [bold]version[/bold] v{snap.version}\n"
            f"[bold]state[/bold]   {snap.current_state}\n"
            f"\n"
            f"queued: [yellow]{snap.queued}[/yellow]   "
            f"assigned: [yellow]{snap.assigned}[/yellow]   "
            f"running: [green]{snap.running}[/green]   "
            f"completed: [cyan]{snap.completed}[/cyan]\n"
            f"failed: [red]{snap.failed}[/red]   "
            f"need-upload: [magenta]{snap.needs_user_upload}[/magenta]   "
            f"need-confirm: [magenta]{snap.needs_user_confirmation}[/magenta]   "
            f"rights: [red]{snap.rights_review_required}[/red]\n"
            f"\n"
            f"[bold]gate[/bold]    {gate}\n"
            f"[bold]next[/bold]    {next_action}\n"
            f"[dim]total tasks: {snap.total}[/dim]"
        )
        self.update(text)


class GatePanel(RichLog):
    """승인 게이트 화면 (v3.0.0, 16 §5) — orchestrator.gate_view 텍스트. 게이트가 아니면 다음 행동만."""

    DEFAULT_CSS = """
    GatePanel {
        border: round $warning;
        height: 2fr;
    }
    """

    def __init__(self) -> None:
        super().__init__(highlight=False, markup=False, wrap=True, max_lines=2000)
        self.border_title = "Gate"

    def show(self, title: str, text: str) -> None:
        self.border_title = title
        self.clear()
        for line in text.splitlines():
            self.write(line)


class WorkerSlotPanel(RichLog):
    """오른쪽 Worker Slot Panel 한 개."""

    DEFAULT_CSS = """
    WorkerSlotPanel {
        border: round $accent;
        height: 1fr;
    }
    """

    def __init__(self, slot_id: int) -> None:
        super().__init__(highlight=False, markup=True, wrap=True, max_lines=500)
        self.slot_id = slot_id
        self.border_title = f"Worker Slot {slot_id} · idle"

    def update_status(self, slot: WorkerSlot) -> None:
        status = slot.status if isinstance(slot.status, str) else slot.status.value
        worker = slot.assigned_worker or "-"
        task_id = slot.assigned_task_id or "-"
        style = STATUS_STYLES.get(status, "white")
        self.border_title = (
            f"Worker Slot {self.slot_id} · [{style}]{status}[/{style}]"
            f" · {worker} · {task_id}"
        )


class CommandCenterApp(App[None]):
    """방식 B Orchestrator Command Center 단일 TUI."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #body {
        height: 1fr;
        width: 100%;
    }
    #left {
        width: 40%;
        min-width: 32;
    }
    #right {
        width: 60%;
    }
    .left-top {
        height: 1fr;
    }
    .left-bottom {
        height: 14;
    }
    .slot-grid {
        height: 1fr;
    }
    .slot-row {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit_app", "quit", priority=True),
        Binding("r", "reload_queue", "reload queue"),
        Binding("s", "save_snapshot", "save snapshot"),
        Binding("f5", "force_refresh", "refresh"),
        Binding("g", "advance", "advance(engine)"),
        Binding("a", "approve_gate", "approve"),
        Binding("x", "reject_gate", "reject"),
    ]

    def __init__(
        self,
        project_id: str,
        project_dir: Path,
        cfg: AppConfig,
        current_state: str = "created",
    ) -> None:
        super().__init__()
        self.project_id = project_id
        self.project_dir = project_dir
        self.cfg = cfg
        self.current_state = current_state

        self.orch_log: OrchLogPanel | None = None
        self.dashboard: DashboardPanel | None = None
        self.slot_panels: dict[int, WorkerSlotPanel] = {}
        self.manager: WorkerSlotManager | None = None
        self._tick_task: asyncio.Task[None] | None = None
        self.gate_panel: GatePanel | None = None
        self.reject_input: Input | None = None
        self._gate_shown: dict[str, str] = {}
        self._gate_state: str = ""
        self._busy: bool = False

    # -----------------------------------------------------------------
    # 레이아웃
    # -----------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="body"):
            with Horizontal():
                with Vertical(id="left"):
                    self.orch_log = OrchLogPanel()
                    yield self.orch_log
                    self.dashboard = DashboardPanel()
                    yield self.dashboard
                    self.gate_panel = GatePanel()
                    yield self.gate_panel
                    self.reject_input = Input(placeholder="반려: <script_draft|direction|assets> <사유> — Enter", id="reject")
                    self.reject_input.display = False
                    yield self.reject_input

                with Vertical(id="right"):
                    yield from self._compose_slot_grid()

        yield Footer()

    def _compose_slot_grid(self) -> ComposeResult:
        n = self.cfg.command_center.worker_slot_count
        # 2 x ceil(n/2) 그리드를 row 단위로 만듭니다.
        rows: list[list[int]] = []
        i = 1
        while i <= n:
            row = [i]
            if i + 1 <= n:
                row.append(i + 1)
            rows.append(row)
            i += 2

        with Vertical(classes="slot-grid"):
            for row in rows:
                with Horizontal(classes="slot-row"):
                    for slot_id in row:
                        panel = WorkerSlotPanel(slot_id=slot_id)
                        self.slot_panels[slot_id] = panel
                        yield panel

    # -----------------------------------------------------------------
    # 라이프사이클
    # -----------------------------------------------------------------

    async def on_mount(self) -> None:
        self.title = f"Orchestrator Command Center · v{__version__}"
        self.sub_title = f"project: {self.project_id}"

        # log_callback / state_listener 등록 후 manager 생성
        self.manager = WorkerSlotManager(
            project_id=self.project_id,
            project_dir=self.project_dir,
            cfg=self.cfg,
            log_callback=self._on_worker_log,
            state_listener=self._on_slots_change,
        )

        self._orch_emit("system", f"Command Center started · v{__version__}")
        self._orch_emit("system", f"project dir: {self.project_dir}")
        self._orch_emit("system", f"worker slots: {self.cfg.command_center.worker_slot_count}")
        self._refresh_dashboard()
        self._refresh_all_slot_status()

        self._tick_task = asyncio.create_task(self._tick_loop())

    async def on_unmount(self) -> None:
        if self._tick_task is not None:
            self._tick_task.cancel()
            try:
                await self._tick_task
            except asyncio.CancelledError:
                pass
        if self.manager is not None:
            await self.manager.shutdown()

    # -----------------------------------------------------------------
    # 주기 tick
    # -----------------------------------------------------------------

    async def _tick_loop(self) -> None:
        assert self.manager is not None
        interval = self.cfg.command_center.tui_refresh_interval_sec
        while True:
            try:
                await self.manager.tick()
                self._reload_manifest_state()
                self._refresh_dashboard()
            except Exception as e:  # noqa: BLE001
                self._orch_emit("stderr", f"tick error: {e}")
            await asyncio.sleep(interval)

    def _reload_manifest_state(self) -> None:
        """매 tick 마다 디스크 manifest 를 다시 읽어 current_state 를 라이브 반영.

        외부 프로세스 (`python -m orchestrator.main transition ...`) 가 manifest 를
        갱신해도 TUI 가 즉시 따라잡도록 한다.

        실패 모드별:
        - 매니페스트 자체가 사라짐 (`FileNotFoundError`) → `unknown` 표시.
        - 손상·옛 버전 manifest (`ManifestError`, v3.0.0) → `invalid` 표시와 오류 로그.
          created 로 폴백하지 않는다(15 P6).
        - 상태 안정될 때까지 stderr noise 를 줄이기 위해 새 진입 시 1회만 로그.
        - 본 메서드는 모든 예외를 swallow 하므로 tick loop 를 죽이지 않는다.
        """
        try:
            manifest = load_manifest(self.project_id, self.cfg)
        except FileNotFoundError:
            if self.current_state != "unknown":
                self._orch_emit(
                    "stderr",
                    f"project_manifest.json 이 사라졌습니다: {self.project_id}",
                )
            self.current_state = "unknown"
            return
        except ManifestError as e:
            if self.current_state != "invalid":
                self._orch_emit(
                    "stderr",
                    f"manifest 파싱 실패 (재시도 예정): {type(e).__name__}: {e}",
                )
            self.current_state = "invalid"
            return

        new_state = manifest.current_state
        if isinstance(new_state, ProjectState):
            new_state = new_state.value
        if new_state != self.current_state:
            self._orch_emit(
                "system",
                f"state changed: {self.current_state} → {new_state}",
            )
            self.current_state = new_state

    # -----------------------------------------------------------------
    # 콜백
    # -----------------------------------------------------------------

    def _on_worker_log(self, slot_id: int, kind: str, line: str) -> None:
        panel = self.slot_panels.get(slot_id)
        if panel is None:
            return
        color = "red" if kind == "stderr" else "yellow" if kind == "system" else "white"
        panel.write(f"[{color}][{kind}][/{color}] {line}")

    def _on_slots_change(self, snapshot: WorkerSlotsSnapshot) -> None:
        for slot in snapshot.slots:
            panel = self.slot_panels.get(slot.slot_id)
            if panel is not None:
                panel.update_status(slot)

    # -----------------------------------------------------------------
    # 화면 갱신 헬퍼
    # -----------------------------------------------------------------

    def _orch_emit(self, kind: str, line: str) -> None:
        if self.orch_log is None:
            return
        ts = datetime.now().strftime("%H:%M:%S")
        color = "red" if kind == "stderr" else "yellow" if kind == "system" else "white"
        self.orch_log.write(f"[dim]{ts}[/dim] [{color}][{kind}][/{color}] {line}")

    def _refresh_dashboard(self) -> None:
        if self.manager is None or self.dashboard is None:
            return
        gate = self.current_state if self.current_state in {g.value for g in GATES} else None
        try:
            action = next_action(self.current_state)
        except ValueError:
            action = None
        snap = DashboardSnapshot.from_queue(
            project_id=self.project_id,
            current_state=self.current_state,
            queue=self.manager.task_queue,
            version=__version__,
            current_gate=gate,
            next_action=action,
        )
        self.dashboard.snapshot = snap
        self._refresh_gate_panel()

    def _refresh_gate_panel(self) -> None:
        """상태가 바뀌었을 때만 게이트 화면을 다시 만든다(린트 CLI 호출 비용)."""
        if self.gate_panel is None or self._gate_state == self.current_state:
            return
        self._gate_state = self.current_state
        if self.current_state in {g.value for g in GATES}:
            try:
                text, self._gate_shown = gate_view(self.project_dir, self.current_state)
            except Exception as e:  # noqa: BLE001 — 화면 오류는 표시하고 죽지 않는다
                text, self._gate_shown = f"게이트 화면 오류: {type(e).__name__}: {e}", {}
            self.gate_panel.show(f"Gate · {self.current_state} · a 승인 / x 반려", text)
        else:
            self._gate_shown = {}
            try:
                action = next_action(self.current_state)
            except ValueError:
                action = "-"
            self.gate_panel.show(f"State · {self.current_state}", f"다음: {action}\n(g = 엔진 단계 실행)")

    def _refresh_all_slot_status(self) -> None:
        if self.manager is None:
            return
        for slot in self.manager.snapshot.slots:
            panel = self.slot_panels.get(slot.slot_id)
            if panel is not None:
                panel.update_status(slot)

    # -----------------------------------------------------------------
    # 단축키 액션
    # -----------------------------------------------------------------

    async def action_quit_app(self) -> None:
        self._orch_emit("system", "quit requested · shutting down workers...")
        await self.action_quit()

    def action_reload_queue(self) -> None:
        if self.manager is None:
            return
        self.manager.reload_queue()
        self._orch_emit("system", "task_queue.json reloaded")
        self._refresh_dashboard()

    def action_save_snapshot(self) -> None:
        if self.manager is None:
            return
        self.manager.save_snapshot()
        self.manager.save_queue()
        self._orch_emit("system", "worker_slots.json / task_queue.json saved")

    def action_advance(self) -> None:
        if self._busy:
            self._orch_emit("system", "advance 진행 중")
            return
        self._busy = True
        self._orch_emit("system", f"advance: {self.current_state}")
        self.run_worker(self._advance_thread, thread=True, exclusive=True)

    def _advance_thread(self) -> None:
        def emit(res: object) -> None:
            r = res  # StageResult
            line = f"StageResult {r.stage} ok={r.ok} drops={len(r.drops)} errors={r.errors[:2]}"  # type: ignore[attr-defined]
            self.call_from_thread(self._orch_emit, "system" if r.ok else "stderr", line)  # type: ignore[attr-defined]
        try:
            m, _ = advance(self.project_id, self.cfg, on_result=emit)
            self.call_from_thread(self._orch_emit, "system", f"state → {m.current_state}")
        except Exception as e:  # noqa: BLE001
            self.call_from_thread(self._orch_emit, "stderr", f"advance: {type(e).__name__}: {e}")
        finally:
            self._busy = False

    def action_approve_gate(self) -> None:
        if self.current_state not in {g.value for g in GATES}:
            self._orch_emit("stderr", f"'{self.current_state}' 는 승인 게이트가 아니다")
            return
        try:
            m = approve_gate(load_manifest(self.project_id, self.cfg), self.current_state,
                             by="command-center", shown=self._gate_shown, cfg=self.cfg)
            self._orch_emit("system", f"승인: {self.current_state} → {m.current_state}")
        except Exception as e:  # noqa: BLE001
            self._orch_emit("stderr", f"approve: {e}")

    def action_reject_gate(self) -> None:
        if self.current_state not in {g.value for g in GATES} or self.reject_input is None:
            self._orch_emit("stderr", f"'{self.current_state}' 는 승인 게이트가 아니다")
            return
        self.reject_input.display = True
        self.reject_input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "reject" or self.reject_input is None:
            return
        self.reject_input.display = False
        to, _, comment = event.value.strip().partition(" ")
        event.input.value = ""
        try:
            m = reject_gate(load_manifest(self.project_id, self.cfg), self.current_state, to,
                            by="command-center", comment=comment, shown=self._gate_shown, cfg=self.cfg)
            self._orch_emit("system", f"반려: {self.current_state} → {m.current_state} ({comment})")
        except Exception as e:  # noqa: BLE001
            self._orch_emit("stderr", f"reject: {e}")

    def action_force_refresh(self) -> None:
        self._refresh_dashboard()
        self._refresh_all_slot_status()
