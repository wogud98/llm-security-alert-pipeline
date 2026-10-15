# LLM 보안 경보 요약 파이프라인

보안 경보 목록을 LLM(Gemini API)으로 요약·위험도 분류하고, 위험한 순서로 정리한 보고서를 만들어 알림 서버로 전송하는 Python 파이프라인입니다. `python pipeline.py` 한 번으로 처음부터 끝까지 실행됩니다.

> **SKT ALEPH 교육 과정(보안·AI 활용)의 실습 프로젝트입니다.** 교육에서 제시된 기본 틀 위에서 구현·테스트·디버깅을 진행했으며, 직접 한 부분은 아래 [직접 구현·수정한 부분](#직접-구현수정한-부분)에 따로 적었습니다. 경보 데이터는 모두 실습용 가상 데이터입니다.

## 동작 흐름

```
events_sample.json (경보 6건)
   │
   ▼  event_summarizer.py   6건씩 묶어 LLM에 전송 → JSON 요약(id, risk_level, summary)
   │
   ▼  sort_by_risk          high → medium → low 순 정렬
   │
   ▼  report_generator.py   LLM 총평 + 코드가 센 건수로 Markdown 보고서 생성·저장
   │
   ▼  notifier.py           사람 확인이 필요한 건수를 알림 서버(webhook)로 전송
```

숫자(전체 건수, high 건수)는 LLM이 아니라 **코드가 직접 세고**, LLM은 요약과 총평 문장만 맡습니다. LLM이 숫자를 틀려도 보고서의 수치는 틀리지 않게 하려는 설계입니다.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `llm_client.py` | Gemini API 호출, `.env`에서 API 키 읽기, LLM 응답(코드 블록에 싸인 JSON)을 딕셔너리로 변환 |
| `event_summarizer.py` | 경보를 묶음으로 나눠 요약하고 위험도순으로 정렬 |
| `report_generator.py` | 총평 요청, 보고서 문자열 생성, 날짜가 든 파일로 저장 |
| `notifier.py` | 설정 파일 검사, 사람 확인 대상 판정, 알림 전송 |
| `pipeline.py` | 위 모듈을 이어 명령 한 번으로 실행 |
| `alert_server.py` | 알림을 받는 로컬 Flask 서버 (테스트용) |
| `test_agent_core.py` | `assert` 기반 단위 테스트 9건 |
| `config.json` | 모델, 확인 기준 위험도, 보고서 폴더, 알림 주소 |
| `events_sample.json` | 실습용 가상 경보 6건 |

## 실행 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. API 키 설정 (.env 는 .gitignore 에 포함되어 있어 커밋되지 않습니다)
cp .env.example .env
# .env 파일을 열어 GEMINI_API_KEY 값을 본인 키로 바꿉니다

# 3. (선택) 알림을 받을 서버를 다른 터미널에서 실행
python alert_server.py

# 4. 파이프라인 실행
python pipeline.py
```

실행하면 `daily_report_YYYYMMDD.md` 보고서가 생성되고, 알림 서버가 켜져 있으면 터미널에 알림 내용이 찍힙니다.

### 테스트 (API 키 없이 실행 가능)

```bash
python test_agent_core.py
# [테스트 통과] 9건 모두
```

테스트 대상은 `make_lines`(보고서 줄 만들기), `needs_approval`(확인 대상 판정), `parse_llm_json`(LLM 응답 파싱)입니다.

## 설계 포인트

- **묶음 처리**: 경보를 6건씩 묶어 보냅니다(`SIZE = 6`). 사용한 무료 키가 분당 15회로 제한되어 있고, 한 번에 많이 보내면 응답 형식이 깨질 수 있기 때문입니다.
- **LLM 응답 방어**: LLM은 JSON을 ` ```json ` 코드 블록으로 감싸 보내는 경우가 많아, 블록 표시를 제거한 뒤 파싱합니다. 파싱에 실패하면 `None`을 돌려주고, 요약 단계는 빈 리스트로 처리해 **다음 묶음을 계속 진행**합니다.
- **실패를 숨기지 않음**: API 호출이 실패하면(429 등) 상태 코드를 출력하고, 총평을 받지 못하면 보고서에 "총평을 만들지 못했습니다"라고 명시합니다.
- **알림이 실패해도 보고서는 남음**: 알림 전송은 `try/except`와 5초 timeout으로 감싸 실패해도 파이프라인이 멈추지 않습니다.
- **설정 분리와 검사**: 모델 이름, 확인 기준, 알림 주소를 `config.json`으로 분리했고, 필수 키가 빠지면 실행 전에 어떤 키가 빠졌는지 알리고 중단합니다.
- **모르는 위험도는 high로 취급**: `needs_approval`은 처음 보는 위험도 값을 high로 보고 사람 확인 대상으로 분류합니다. 놓치는 것보다 묻는 쪽이 안전하다는 판단입니다.
- **비밀 정보 관리**: API 키는 코드에 쓰지 않고 `.env`에서 읽으며, `.env`는 `.gitignore`로 제외했습니다.


## 사용 기술

Python, requests, Flask, Gemini API(OpenAI 호환 엔드포인트), JSON, `assert` 기반 단위 테스트
