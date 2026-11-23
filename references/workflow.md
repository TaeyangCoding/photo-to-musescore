# MuseScore에서 확인된 작업 방법

## 실행 환경과 스타일

최초 검증 환경은 macOS의 MuseScore Studio 4.7.6이다. macOS 기본 실행 파일은 `/Applications/MuseScore 4.app/Contents/MacOS/mscore`이며, Linux·Windows에서는 설치한 MuseScore의 실제 실행 파일을 사용한다. 실제 `--help`를 확인하고 필요한 옵션만 사용한다. 공장 초기화 옵션은 사용하지 않는다. 아래 `mscore`는 해당 실행 파일을 뜻한다.

MusicXML을 가져올 때 글꼴이 기본값으로 덮이는 경우가 있었다. 사보한 MusicXML을 전용 작업 디렉터리의 MSCX로 변환하고, 네이티브 MSCX에 헤더·마디 수정을 반영한 다음, 그 MSCX에 번들 MSS를 `-S`로 적용하면서 MSCZ로 저장한다. **그 MSCZ를 다시 열어** PDF·PNG를 출력한다.

```
mscore input.musicxml -o work/imported.mscx
mscore work/imported.mscx -S /absolute/path/to/assets/score-style.mss -o output.mscz
mscore output.mscz -o output.pdf
mscore output.mscz -r 240 -o output.png
```

MuseScore 4.7의 MSCX는 `score_style.mss`, `META-INF/`, 오디오·보기 설정 등을 옆 파일로 저장할 수 있다. 작업마다 디렉터리를 분리한다. MSCX 한 파일만 옮기고 스타일도 포함됐다고 생각하지 않는다. 최종 편집본은 **MSCZ**로 전달한다.

## 제목과 크레딧

네이티브 XML의 `Score/Staff/VBox/Text`에서 스타일은 `title`, `subtitle`, `composer`, `poet`로 확인됐다.

- `composer`의 `text`에 `임선호 작곡\n김준영 작사`처럼 두 줄을 넣으면 오른쪽에 쌓인다. 재저장 후 `<br/>` 요소로 바뀔 수 있으니 검증 시 `findtext()`만 쓰지 말고 자식 텍스트도 합쳐 읽는다.
- `poet` 텍스트에 사용자가 지정한 사보자 크레딧을 넣어 왼쪽에 둔다. 원래 작사가는 메타데이터와 오른쪽 크레딧에 유지한다.
- VBox 높이는 제목·부제·두 줄 크레딧을 보고 조정한다. 승인 예시는 14sp였지만 새 곡의 긴 제목에 고정하지 않는다.
- 최초 검증 때 `Xingkai TC`가 없는 환경에서 SFNS로 대체되는 문제가 있었다. 번들 스타일은 `Brush Script MT`를 사용한다. 해당 글꼴이 실제 설치됐는지 확인하고 PDF의 `/BrushScriptMT` 사용도 확인한다.

## 줄을 넘는 못갖춤 부분

UI의 마디 분할 또는 MusicXML에서 분할한 뒤 MuseScore로 다시 가져오는 방법을 쓴다. 네이티브 XML을 직접 나누면 Tie/Slur의 상대 위치 참조도 갱신해야 하므로, 검증 없이 요소만 잘라 옮기지 않는다.

- MusicXML 노트·쉼표를 구절 시작 시각에서 앞/뒤 마디로 나눈다. 노트 중간이면 길이 분할과 tie 처리를 명시해야 한다.
- 뒤 조각에 `implicit="yes"`, `<print new-system="yes"/>`를 둔다. harmony offset은 분할 시각을 빼서 다시 계산한다. 원래 다음 마디의 새 줄 지시는 제거한다.
- 앞 조각 끝의 불필요한 새 세로줄은 `<barline location="right"><bar-style>none</bar-style></barline>`로 숨길 수 있다.
- 네이티브 MSCX에서 실제 길이가 `<Measure len="5/8">`와 뒤쪽 `<Measure len="3/8"><irregular>1</irregular>`처럼 보존됐는지 확인한다.
- 못갖춤 다음 온마디의 줄 중간 번호는 해당 Measure의 `<measureNumberMode>2</measureNumberMode>`로 숨긴다. 정상적인 줄 시작 번호까지 일괄 없애지 않는다.
- `<BarLine><subtype>double</subtype>`는 필요한 경우에만 `normal`로 바꾼다. 마지막 `end` 세로줄은 유지한다.

승인 예시 「주를 위한 이곳에」에서는 원래 16·24마디를 **2.5 + 1.5박**, 20·28마디를 **3.5 + 0.5박**으로 나눴다. 다음 줄에 각각 ‘주 은혜’, ‘그’를 붙였다. 이 숫자는 다른 곡의 분할 규칙이 아니다.

## 보조 도구

Python 표준 라이브러리와 MuseScore를 사용한다. 입력은 스타일과 가독성 수정을 마친 네이티브 MSCZ다.

```
python3 scripts/render_variants.py baseline.mscz \
  --mscore /absolute/path/to/mscore \
  --out-dir /absolute/task/outputs/조별악보 --name '곡명' \
  --keys C D Eb E F \
  --shifts C=-2 D=0 Eb=1 E=2 F=3 --zip
```

위 목록은 **D장조 기준의 사용 예시**이며 고정 추천 조가 아니다. 원조·음역과 사용자의 요청에 맞게 정한다. `--shifts`가 없으면 가까운 음역으로 조옮김한다. `--keys`가 없으면 원조만 출력한다. 장조가 아니거나 조성이 불분명하면 에이전트가 원곡 문맥에 맞는 방법으로 처리한다. Linux의 GUI 없는 환경에서는 정상적인 Qt 실행 환경이 필요하며, 지원되는 경우 `QT_QPA_PLATFORM=offscreen`을 사용할 수 있다.

새 출력 디렉터리를 사용한다. 도구는 기존 파일을 덮지 않는다. 실제 조표, 모든 노트의 동일 음정 이동, 코드 루트·베이스 이동, 가사·리듬·줄바꿈·부분 마디 길이를 검사한다. 사보 정확성과 시각적 품질은 별도로 검토한다.

macOS 한글 파일명의 NFC/NFD 차이 때문에 glob이 비어 보일 수 있었다. 중간 PNG는 ASCII 이름을 쓰고, 최종 파일은 한 페이지면 `곡명_조.png`, 여러 페이지면 `곡명_조_p01.png` 순서로 보존한다.

PDF는 MuseScore에서 직접 출력하고 모든 페이지를 렌더링해 확인한다. PDF 렌더링 도구는 현재 환경에서 이용 가능한 것을 사용하며, 특정 에이전트의 플러그인을 필수로 가정하지 않는다. 다른 원본 악보 폴더의 재구성·수정은 이 과정에 포함하지 않는다.
