# 사진을 뮤즈스코어 악보로 변환

악보 사진이나 스캔 이미지를 보내면, 에이전트가 음표·리듬·코드·가사를 읽어 **편집 가능한 MuseScore 악보**로 사보하는 스킬입니다.

## 결과물

- MSCZ: MuseScore에서 수정할 수 있는 원본
- PDF: 인쇄·보관용
- PNG: 모든 페이지의 검토용 이미지

세 형식을 모두 준비하고, 기본 검토 메시지에는 **PNG만 제시**합니다. PDF·MSCZ는 요청할 때 전달합니다. 기본적으로 원조 한 개를 제작하며, 추가 조는 요청·승인받은 범위에서 만듭니다.

## 필요한 환경

- 악보 이미지를 볼 수 있는 에이전트와 로컬 파일 읽기·쓰기 기능
- MuseScore Studio 4 실행 환경
- 보조 출력 도구를 사용할 경우 Python 3
- 선호 서체: DX시인과나, Brush Script MT

폰트 파일과 실제 악보 사진·사보 결과물은 포함하지 않습니다. 필요한 폰트는 사용 권한이 있는 파일을 직접 설치해야 합니다. 폰트가 없으면 원래 스타일과 동일하게 출력되지 않을 수 있습니다.

이 저장소는 **에이전트용 작업 지침과 스타일, 출력 보조 도구**입니다. 사진을 자동 인식하는 독립 OMR 프로그램은 포함하지 않습니다. 에이전트가 사진을 판독해 MusicXML/MSCX로 사보한 다음 MuseScore에서 MSCZ로 저장합니다. `render_variants.py`는 완성한 MSCZ의 장조 조옮김·출력용입니다.

## OpenClaw에 설치

OpenClaw의 [공식 스킬 문서](https://docs.openclaw.ai/tools/skills)에 따라, 다음처럼 공유 스킬 폴더에 설치할 수 있습니다.

```sh
mkdir -p "$HOME/.openclaw/skills"
git clone https://github.com/TaeyangCoding/photo-to-musescore.git "$HOME/.openclaw/skills/photo-to-musescore"
```

이미 같은 이름의 폴더가 있으면 덮어쓰지 말고 기존 변경을 확인·보관한 뒤 갱신하세요. 현재 OpenClaw의 스킬 목록 또는 `openclaw skills check`에서 인식 여부를 확인하고 새 대화에서 사용합니다. 에이전트별 스킬 허용 목록을 쓰는 환경에서는 해당 에이전트에 이 스킬을 허용해야 합니다.

Codex에서는 같은 저장소를 `~/.codex/skills/photo-to-musescore`에 설치할 수 있습니다. `agents/openai.yaml`은 Codex용 표시 정보이며, 핵심 지침은 공통 `SKILL.md`에 있습니다.

## 사용 예시

악보 사진을 첨부하고 다음처럼 요청합니다.

> 이 악보 사진을 photo-to-musescore 스킬로 편집 가능한 뮤즈스코어 악보로 변환해줘. MSCZ·PDF·PNG를 준비하고, 검토할 때는 PNG만 보여줘.

특정 조가 필요하면 곡의 조와 옥타브·음역 조건을 함께 적습니다. 조 추천을 요청하면 기준 조를 포함해 약 5개를 제안하며, 검토·승인 절차가 있는 작업에서는 나머지 조를 승인 후 제작합니다.

## 스타일과 범위

- A4 세로, 사방 약 15mm 여백
- 제목·가사: DX시인과나, 영문 부제: Brush Script MT
- 작곡·작사 및 사용자가 지정한 사보자 크레딧 표기
- 보컬 문장이 끊기지 않도록 못갖춤 부분과 줄바꿈 조정
- 원본과 모든 출력 페이지를 대조하고, 판독이 불확실한 부분은 명시

제목·크레딧 등 사용자 요청이 있으면 그 요청을 우선합니다. 곡 선정, 참고 악보 자동 검색, Telegram 전송, 예약 업무, Notion 기록, 블로그 게시 기능은 포함하지 않습니다.

## 출력 보조 도구

스타일과 사보 검수를 마친 장조 MSCZ를 입력합니다. MuseScore 실행 파일 위치는 실제 환경에 맞게 지정합니다.

```sh
python3 scripts/render_variants.py baseline.mscz \
  --mscore /absolute/path/to/mscore \
  --out-dir /absolute/path/to/new-output-directory \
  --name '곡명' --zip
```

`--keys`를 생략하면 원조만 출력합니다. 추가 조 제작을 요청받았을 때만 `--keys`를 지정합니다. 도구는 기존 파일을 덮지 않으며, 음높이 이동·리듬·가사·코드와 부분 마디를 검사합니다. 사진 사보 정확성과 최종 가독성은 별도 검수가 필요합니다.

상세 작업 방법: [SKILL.md](SKILL.md), [references/workflow.md](references/workflow.md).
