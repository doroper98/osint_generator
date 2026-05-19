@echo off
REM longform-briefing-pipeline 진입 스크립트 (Windows)
REM 사용법:
REM   run_pipeline.bat                            -> demo 프로젝트로 Command Center 진입
REM   run_pipeline.bat {project_id}               -> 지정 프로젝트로 진입
REM   run_pipeline.bat new "주제" {category} {min} -> 새 프로젝트 생성 후 진입

setlocal enabledelayedexpansion

REM 가상환경 자동 활성화 (있을 때만)
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)

REM PYTHONPATH에 저장소 root 추가
set PYTHONPATH=%cd%;%PYTHONPATH%

if "%1"=="" (
  python -m orchestrator.main command-center --project demo
  goto :eof
)

if "%1"=="new" (
  python -m orchestrator.main new-project --title %2 --category %3 --duration-min %4
  goto :eof
)

python -m orchestrator.main command-center --project %1
