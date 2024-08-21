# AI Agent

pdf를 내용을 기반으로 답변해주는 LLM 어플리케이션


## 구성
- Python 3.11
- Langchain
- Chroma (or Pinecone)
- FastAPI + Python Dependency Injector
- Redis
- Docker

---


## 환경변수

### 1. .env 파일을 생성해주세요.
### 2. 아래 환경변수를 넣어주세요. 
./app/settings안에 매핑되어 들어갑니다
```dotenv
OPENAI_API_KEY=...
PINECONE_API_KEY=...
```

---


## 로컬에서 실행 방법

✅ **1.은 이미 처리되어 있으니 2. -> 3. 순으로 실행해주세요.** (실행한 경우 사용하지 않을 이미지를 수동으로 지워야합니다.)

✅ **2.은 최초 한번만 실행하면 됩니다.**

✅ 그 이후로 띄울때는 **3.만 실행**하면 됩니다.

### 1. (Optional) pdf를 마크 다운으로 변환 후 이미지 지우기
```shell
make pdf_to_markdown
```

### 2. chunk로 vectorstore에 저장
```shell
make load_vectorstore type=chroma
```

### 3. 이미지 down, build, up, logs
```shell
make dbul
```

---

## URL

Streamlit: http://localhost:8501

API: http://localhost:5000/api/docs

---

## Test
```shell
make test
```

---
