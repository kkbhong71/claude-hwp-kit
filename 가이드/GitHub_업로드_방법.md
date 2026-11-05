# 키트를 GitHub에 올려 공유하는 방법 (배포하는 사람용)

## 1. 왜 GitHub에 올리나요?

- 주소 하나만 알려 주면 누구나 최신 버전을 내려받을 수 있다.
- 키트를 고치면 GitHub의 파일만 바꾸면 되므로, 여러 사람에게 파일을 다시 보낼 필요가 없다.
- 받는 사람은 Claude Code에 주소만 붙여 넣어 설치를 맡길 수도 있다.

## 2. 준비

1. github.com 에 접속해 오른쪽 위 'Sign up'으로 무료 계정을 만든다. (이미 있으면 로그인)
2. 이 키트 폴더(claude-hwp-kit)가 내 PC에 있는지 확인한다.

## 3. 저장소 만들기

1. GitHub 오른쪽 위의 '+' 버튼을 누르고 'New repository'를 선택한다.
2. Repository name에 claude-hwp-kit 을 입력한다.
3. 공개 범위를 고른다. 누구나 받게 하려면 Public, 초대한 사람만 받게 하려면 Private을 고른다.
4. 다른 항목은 그대로 두고 아래 'Create repository' 버튼을 누른다.

## 4. 파일 올리기 (웹 화면에서 끌어다 놓기)

1. 새로 만든 저장소 화면에서 'uploading an existing file' 링크를 누른다.
2. 탐색기에서 claude-hwp-kit 폴더를 열고, 안의 파일과 폴더를 모두 선택해 브라우저 화면으로 끌어다 놓는다.
3. 업로드 목록이 다 올라가면 아래 'Commit changes' 버튼을 누른다.
4. 저장소 첫 화면에 README 안내문이 보이면 완료다.

> 폴더째 끌어다 놓아야 skill, 가이드, 예시 폴더 구조가 유지됨. 크롬·엣지 브라우저 사용을 권장함.

## 5. 다른 선생님께 안내하기

| 받는 분의 상황 | 알려 줄 내용 |
|---|---|
| 처음 쓰는 분 | 저장소 주소 + '초록색 Code 버튼 → Download ZIP → 설치하기.bat 실행' |
| Claude Code에 익숙한 분 | 'github.com/내계정/claude-hwp-kit 키트를 내려받아서 install.ps1로 설치해 줘' 문장 |
| GitHub 접속이 어려운 분 | claude-hwp-kit.zip 파일을 메신저·메일로 직접 전달 |

## 6. 키트를 고친 뒤 다시 올리기

1. 저장소 화면에서 'Add file' → 'Upload files'를 누른다.
2. 바뀐 파일을 같은 위치에 끌어다 놓으면 기존 파일이 새 파일로 바뀐다.
3. 'Commit changes'를 누른다.

> Claude Code에게 "이 키트를 GitHub 저장소에 올려 줘"라고 요청해도 됨. 처음 한 번은 GitHub 로그인 과정이 필요함.
