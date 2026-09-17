# GitHub(https://github.com/ll3i) 업로드 가이드

프로젝트를 [ll3i](https://github.com/ll3i) 계정의 저장소에 올리는 방법입니다.

---

## 1. GitHub에서 새 저장소 만들기

1. [https://github.com/new](https://github.com/new) 접속 후 로그인
2. **Repository name**: 예) `산업AI_Agent_해커톤` 또는 `industry-ai-agent-hackathon` (영문 권장)
3. **Public** 선택
4. **"Add a README file"** 은 체크하지 말고 **Create repository** 만 클릭  
   (이미 로컬에 코드가 있으므로)
5. 생성된 저장소 URL 확인  
   - `https://github.com/ll3i/저장소이름`  
   - 예: `https://github.com/ll3i/industry-ai-agent-hackathon`

---

## 2. 로컬에서 터미널(또는 Git Bash)로 실행

**프로젝트 폴더**로 이동한 뒤 아래를 순서대로 실행하세요.

```bash
cd "c:\Users\work4\OneDrive\바탕 화면\산업AI_Agnet_해커톤"
```

### (1) 원격이 아직 없을 때

```bash
git remote add origin https://github.com/ll3i/저장소이름.git
```

예:

```bash
git remote add origin https://github.com/ll3i/industry-ai-agent-hackathon.git
```

### (2) 이미 다른 origin 이 있을 때

```bash
git remote set-url origin https://github.com/ll3i/저장소이름.git
```

### (3) 현재 브랜치 확인 후 푸시

```bash
git branch
git add .
git status
git commit -m "Upload: 산업AI Agent 해커톤 프로젝트"
git push -u origin main
```

`main` 대신 `master` 를 쓰는 저장소라면:

```bash
git push -u origin master
```

---

## 3. .gitignore 때문에 일부 파일이 안 올라가는 경우

현재 `.gitignore` 에 아래가 있어 **기본적으로는 커밋되지 않습니다.**

- `run_*.py` (run_agent.py, run_v8.py 등)
- `*.ipynb` (ai_agent.ipynb 등)
- `notebooks/`
- `outputs/`, `output*.csv`
- `test/`, `train/` 등

**제출용 코드까지 올리려면** 두 가지 중 하나를 선택하면 됩니다.

### 방법 A: 제출용만 강제로 추가 후 커밋

```bash
git add -f run_agent.py
git add -f run_v8.py
git add -f "notebooks/ai_agent.ipynb"
git add -f requirements.txt
git add -f README.md
git add -f src/
git add -f docs/
git add -f .env.example
git status
git commit -m "Add submission scripts and docs"
git push origin main
```

### 방법 B: .gitignore 에서 제출용 예외 넣기

`.gitignore` 안에 다음처럼 **예외**를 넣은 뒤, 다시 `git add` / `commit` / `push` 합니다.

```gitignore
# 제출용 예외 (주석 해제 후 사용)
!run_agent.py
!run_v8.py
!run_full_analysis.py
!notebooks/ai_agent.ipynb
!outputs/output.csv
```

---

## 4. 요약 체크리스트

- [ ] GitHub 에서 새 저장소 생성 (Public, README 없이)
- [ ] `git remote add origin https://github.com/ll3i/저장소이름.git` (또는 `set-url`)
- [ ] `git add .` 또는 제출용만 `git add -f ...`
- [ ] `git commit -m "메시지"`
- [ ] `git push -u origin main` (또는 `master`)
- [ ] **.env** 는 반드시 제외되고, **.env.example** 만 올라가도록 확인

---

## 5. 한 번에 복사해 쓸 수 있는 명령어 예시

저장소 이름을 `industry-ai-agent-hackathon` 으로 했다고 가정:

```bash
cd "c:\Users\work4\OneDrive\바탕 화면\산업AI_Agnet_해커톤"
git remote add origin https://github.com/ll3i/industry-ai-agent-hackathon.git
git add .
git commit -m "Upload: 산업AI Agent 해커톤"
git push -u origin main
```

이미 `origin` 이 있으면:

```bash
git remote set-url origin https://github.com/ll3i/industry-ai-agent-hackathon.git
git add .
git commit -m "Upload: 산업AI Agent 해커톤"
git push -u origin main
```

`.env`는 `.gitignore`에 포함되어 있는지 꼭 확인한 뒤 푸시하세요.
