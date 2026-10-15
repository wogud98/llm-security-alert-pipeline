import llm_client                                             # llm_client.py 를 불러온다
import notifier                                               # notifier.py 를 불러온다
import report_generator                                       # report_generator.py 를 불러온다

# report_generator.make_lines
# 대문자가 섞인 요약 한 건
sample = [{"id": "E01", "risk_level": "High", "summary": "로그인 실패 4회"}]
# 대문자 위험도 · id · 요약 · 줄바꿈까지 같아야 한다
assert report_generator.make_lines(sample) == "- [HIGH] E01 로그인 실패 4회\n", "make_lines 결과가 다르다"
# 요약이 없으면 줄도 없어야 한다
assert report_generator.make_lines([]) == "", "빈 리스트는 빈 문자열이어야 한다"
two = [{"id": "E02", "risk_level": "low", "summary": "새 IP 로그인"}, {"id": "E03", "risk_level": "medium", "summary": "심야 접속"}]   # 요약 두 건
assert report_generator.make_lines(two).count("\n") == 2, "한 건에 한 줄이어야 한다"   # 두 건이면 두 줄

# notifier.needs_approval
config = {"approve_severity": "high"}                         # 기준만 있으면 판정할 수 있다
# high 는 사람에게 묻는다
assert notifier.needs_approval("high", config) == True, "high 는 확인 대상이어야 한다"
# low 는 묻지 않는다
assert notifier.needs_approval("low", config) == False, "low 는 확인 대상이 아니어야 한다"
# 처음 보는 위험도도 묻는다 — 모를 때는 막는 쪽
assert notifier.needs_approval("critical", config) == True, "모르는 위험도도 확인 대상이어야 한다"

# llm_client.parse_llm_json
fenced = "```json\n{\"tool\": \"lock_account\"}\n```"         # 코드 블록에 싸인 JSON
# 코드 블록을 벗기고 딕셔너리로 읽어야 한다
assert llm_client.parse_llm_json(fenced) == {"tool": "lock_account"}, "코드 블록을 벗기지 못했다"
# JSON 이 아닌 답은 None
assert llm_client.parse_llm_json("그럴듯한 문장입니다") is None, "깨진 입력은 None 이어야 한다"
# 빈 답도 None
assert llm_client.parse_llm_json("") is None, "빈 답은 None 이어야 한다"

print("[테스트 통과] 9건 모두")                                       # 여기까지 오면 아홉 줄이 모두 참이었다
