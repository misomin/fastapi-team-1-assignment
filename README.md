# FastAPI 세미나 과제 4, 5

본 과제에서는 세미나에서 다룬 내용에 대한 추가 조사 및 응용을 요구합니다.  
과제 수행 과정에서 적극적으로 공식 문서를 찾아보고, 질문해보시기를 권유드립니다.

## 진행 방식과 필수 범위

- 와팡 서버를 구현합니다. 조별 저장소 하나에 협업한 결과를 제출합니다.
- 인증·회원가입 등의 기존 코드는 출발점이며, 필요에 따라 수정할 수 있습니다.
- 아래 API와 인프라 요구 사항을 모두 완료해야 합니다.

### 실행 및 테스트

Python 3.12, uv, Docker Compose를 설치하고 Docker를 실행한 뒤 프로젝트 루트에서 진행합니다.

```bash
uv sync --frozen
docker compose up -d --wait
# 모델 작성 및 마이그레이션 스크립트 생성 후 적용
uv run alembic upgrade head
uv run uvicorn wapang.main:app --reload
```

- Compose는 MySQL 8.4와 `wapang` 데이터베이스를 생성합니다. `.env.local`은 `127.0.0.1:3307`, 사용자 `wapang`, 비밀번호 `local-password`로 맞춰져 있어 수정 없이 연결할 수 있습니다. 기존 로컬 MySQL과의 충돌을 줄이기 위해 호스트 포트는 3307을 사용합니다.
- API 서버는 호스트에서 실행하며, Docker에는 DB만 실행합니다. 위 명령은 기본값인 `ENV=local` 기준입니다.
- DB를 중지할 때는 `docker compose down`을 실행합니다. 데이터는 볼륨에 남습니다. **`docker compose down -v`는 로컬 DB 데이터를 모두 삭제**하므로 초기화가 필요할 때만 사용합니다.
- Compose의 DB 계정은 최초 볼륨 생성 시 설정됩니다. 계정 값을 바꿔도 기존 볼륨의 계정은 자동 변경되지 않습니다.

- API 기본 경로는 `/api`이며, 문서는 `http://127.0.0.1:8000/docs`에서 확인합니다.
- 새 모델을 작성한 뒤에는 아래 마이그레이션 안내에 따라 revision을 생성해야 합니다. 템플릿에는 완성된 마이그레이션이 없습니다.

## 과제 목표

- 4주차
  - ER 다이어그램을 활용하여 도메인에 적합한 데이터베이스 모델을 설계할 수 있다.
  - SQLAlchemy를 사용하여 데이터베이스를 다루고 API를 구현할 수 있다.
  - 주문과 재고 처리를 포함한 API를 개발할 수 있다.
  - EC2와 RDS에 서비스를 배포하고, 테스트를 통과한 변경을 자동 배포할 수 있다.
- 5주차
  - API 테스트를 작성할 수 있다.
  - Router - Service - Repository 패턴으로 코드를 작성할 수 있다.

## 준비 사항

- 앞서 학습한 인증과 CRUD를 바탕으로 진행하며, 시작에 필요한 코드는 이 저장소에 제공합니다.

- 이번 과제는 `python 3.12` 버전을 기준으로 하며, `uv`를 이용해 패키지를 관리합니다.
  - `uv venv` 명령어로 가상환경을 생성하고,
  - `uv sync` 명령어로 `uv.lock` 파일에 기본 제공된 라이브러리를 설치해주세요.

- 이번 과제는 **서드파티 라이브러리 추가를 허용**합니다.
  - `pip install` 대신 `uv add`를 이용해 서드파티 라이브러리를 설치하시면 됩니다.
  - `uv add`를 이용해 설치하시면 `pyproject.toml` 파일과 `uv.lock` 파일의 내용이 수정되는데, **이 또한 함께 commit해주셔야 합니다**.
    - 그렇지 않으면 활용하신 라이브러리를 알 수 없어, 과제 채점에 차질이 생길 수 있습니다.

- `uv` 설치 및 사용에 관한 구체적인 내용은 [`uv` 공식문서](https://docs.astral.sh/uv/)를 참조하세요.

## 과제 요구 사항

### 개요

- 로켓배송으로 유명한 와팡의 서버를 개발합니다.
- SQLAlchemy를 사용하여 데이터베이스 모델을 설계하고 API를 구현합니다.
- 제공된 스켈레톤 코드에 얽매일 필요는 없으며, 필요에 따라 파일, 함수 등을 추가 또는 제거하셔도 좋습니다.

### 1. 데이터베이스 모델 설계 (ER 다이어그램)

주어진 요구 사항에 따라 데이터베이스 구조를 설계해봅시다.  
ERD 작성 사이트나 도구에는 제한이 없습니다. 이미지·PDF 파일 또는 채점자가 접근 가능한 링크로 제출해주세요.
ERD는 실제 ORM 모델 및 마이그레이션과 일치해야 하며, 테이블의 PK·FK와 관계를 확인할 수 있어야 합니다.
파일은 저장소에 포함하고, 파일 경로나 링크를 `erd_link.py`의 `ERD_LINK`에 작성해주세요.

- 유저는 `id`, `email`, `hashed_password`, `nickname`, `address`, `phone_number` 을 가지고 있어야 합니다.
- 유저는 최대 하나의 상점만 소유할 수 있습니다.
- 상점은 `id`, `name`, `address`, `email`, `phone_number`, `delivery_fee` 를 가지고 있어야 합니다.
- 상점은 여러 개의 상품을 팔 수 있으며, 각각의 재고를 숫자로 관리합니다.
- 상품은 `id`, `name`, `price`, `stock`을 가지고 있어야 합니다.
- 각 상품은 하나의 상점에 종속되는 것으로 합니다.
- 유저는 여러 개의 주문을 할 수 있습니다.
- 주문은 `id`, `status`, `total_price`를 가지고 있어야 합니다.
- 주문의 `status` 속성은 진행 상태에 따라 `CANCELED`, `ORDERED`, `COMPLETE` 중 하나의 상태를 가집니다.
- 한 주문에는 여러 개의 상품이 포함될 수 있습니다.

### 2. 데이터베이스 구조 작성 및 마이그레이션

1에서 설계한 ER 다이어그램을 바탕으로 SQLAlchemy ORM 모델을 작성하고, 그 구조를 MySQL 데이터베이스에 반영(마이그레이션)합니다. 로컬에서 개발한 뒤 배포 시 RDS MySQL에도 적용해야 합니다.

#### SQLAlchemy ORM 작성

`./wapang/app/auth/models.py`와 `./wapang/app/users/models.py`에 SQLAlchemy ORM 모델의 예시가 제공되어 있습니다.
위 예시와 [SQLAlchemy 공식 문서](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)를 탐구한 후 과제 1의 결과에 적합한 SQLAlchemy ORM 모델을 작성해보세요.

#### alembic을 사용한 마이그레이션

##### 마이그레이션을 위한 환경 설정

마이그레이션에 필요한 환경 변수를 설정하기 위한 골격은 스켈레톤 코드에 함께 제공되었습니다.  
스켈레톤 코드와 [Pydantic Settings 공식 문서](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)를 탐구한 후 SQLAlchemy ORM 모델의 구조와 DB 구조를 연동하기 위한 환경 변수를 설정하세요.

- 참고
  - 제공된 Compose를 사용하면 `.env.local`을 수정할 필요가 없습니다. 별도 MySQL을 사용하는 경우에만 접속 정보를 수정해주세요.
  - 수정하신 `.env.local` 파일을 commit하실 필요는 없습니다(사실 `.env` 파일을 git에 포함시키는 것은 권장되지 않습니다. 본 과제에서는 코드의 골격 제시를 위해 부득이하게 포함하였습니다).
  - `.env.test`는 채점 시 사용되므로 **수정하지 말아주세요.**
  - `.env.prod`는 배포 환경 설정의 예시입니다. RDS 접속 정보와 인증 키는 GitHub Secrets 또는 EC2의 환경변수로 주입하고, 실제 값을 저장소에 커밋하지 마세요.
- 세 파일 중 실제 서버 가동에 사용될 파일을 결정하는 방법은 직접 탐구해보시기 바랍니다!

##### 마이그레이션하기

- 힌트
  - `./wapang/database/alembic/env.py`에서 import문을 통해 SQLAlchemy ORM 모델들이 import되어야 합니다.
  - `uv run alembic revision --autogenerate -m "메시지 내용"` 명령어를 통해 마이그레이션을 위한 스크립트를 자동 생성할 수 있습니다.
  - `uv run alembic upgrade head` 명령어를 통해 작성된 스크립트를 적용할 수 있습니다.

### 3. API 구현

와팡의 회원가입 및 프로필 조회, 수정 API, 상점과 상품 관리 API를 구현해봅시다.  
데이터베이스를 사용하여 유저와 상점과 상품 정보를 저장하고, 조회할 수 있어야 합니다.
인증, 인가가 필요한 API에는 Authorization 헤더의 Bearer 토큰을 활용하며, 토큰 검증에는 제공된 인증 코드를 활용합니다.
로그인을 통한 토큰의 발급 로직은 스켈레톤 코드에 기본 제공되었습니다.

#### 1. `/api/users` 엔드포인트

##### 1-1) POST `/api/users` — 회원가입

- 사용자의 회원 가입 요청을 받아 검증 및 처리하며, 성공 시 데이터베이스에 저장합니다.
- 회원 가입 요청이 들어오면 다음의 사항이 검증돼야 합니다.
  - `email`과 `password`가 모두 있어야 합니다.
  - `email`: 이메일 형식이어야 합니다. 기존에 존재하는 회원과 중복되지 않는지 확인해야 합니다.
  - `password`: 8자 이상 20자 이하여야 합니다.
- 회원가입 성공 시 사용자 정보를 데이터베이스에 저장하며, 비밀번호는 argon2로 해싱하여 저장합니다.
- 각 사용자에게는 고유 식별자인 `id`(str)가 부여됩니다.

- **요청**
  - 본문 예시

    ```json
    {
    	"email": "waffle@example.com",
    	"password": "password1234"
    }
    ```

- **응답**
  - **성공 응답**
    - 상태 코드: 201
    - 본문: 생성된 사용자 정보 (비밀번호 제외)
    - 예시

    ```json
    {
    	"id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    	"email": "waffle@example.com",
    	"nickname": null,
    	"address": null,
    	"phone_number": null
    }
    ```

  - **실패 응답**

    | 상황                                           | 상태 코드 | ERROR_CODE | ERROR_MSG               |
    | ---------------------------------------------- | --------- | ---------- | ----------------------- |
    | 요청 필드가 비어있는 경우                      | 400       | ERR_002    | MISSING REQUIRED FIELDS |
    | 요청 필드의 형식이 올바르지 않은 경우          | 400       | ERR_003    | INVALID FIELD FORMAT    |
    | 같은 이메일의 사용자가 이미 등록되어 있는 경우 | 409       | ERR_004    | EMAIL ALREADY EXISTS    |
    - 예시  
      상태 코드 400과 함께 다음의 본문(application/json)이 반환됨.

      ```json
      {
      	"error_code": "ERR_002",
      	"error_msg": "MISSING REQUIRED FIELDS"
      }
      ```

##### 1-2) GET `/api/users/me` — 프로필 조회 (로그인 필요)

- 서버는 JWT 토큰을 통해 사용자의 신분 증명을 검증한 후, 사용자가 식별되면 해당 사용자의 정보를 응답 본문으로 보냅니다.
- 요청 헤더에 `Authorization: Bearer {access_token}` 형식으로 토큰이 포함되어야 합니다.

- **요청**
  - 헤더에 다음 필드가 포함됨

    ```
    Authorization: Bearer {access_token}
    ```

- **응답**
  - **성공 응답**
    - 상태 코드: 200
    - 본문: 사용자 정보 (비밀번호 제외)
    - 예시

      ```json
      {
      	"id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      	"email": "waffle@example.com",
      	"nickname": "와플이",
      	"address": "서울시 관악구",
      	"phone_number": "010-1234-5678"
      }
      ```

  - **실패 응답**

    | 상황                                           | 상태 코드 | ERROR_CODE | ERROR_MSG                |
    | ---------------------------------------------- | --------- | ---------- | ------------------------ |
    | Authorization 헤더가 제시되지 않은 경우        | 401       | ERR_005    | UNAUTHENTICATED          |
    | Authorization 헤더 값의 형식이 비정상적인 경우 | 400       | ERR_006    | BAD AUTHORIZATION HEADER |
    | 토큰이 유효하지 않은 경우                      | 401       | ERR_007    | INVALID TOKEN            |

##### 1-3) PATCH `/api/users/me` — 프로필 수정 (로그인 필요)

- 로그인한 사용자의 프로필 정보를 수정합니다. 이메일은 수정 대상이 아니며 기존 값을 유지합니다.
- 요청으로 들어온 각 필드는 다음의 방법에 따라 검증돼야 합니다. 또한 적어도 하나 이상의 필드가 포함되어야 합니다.
  - `nickname`: 20자 이하의 문자열이어야 합니다.
  - `address`: 100자 이하의 문자열이어야 합니다.
  - `phone_number`: 010-xxxx-xxxx 형식의 문자열이어야 합니다.

- **요청**
  - 헤더에 다음 필드가 포함됨

    ```
    Authorization: Bearer {access_token}
    ```

  - 본문 예시

    ```json
    {
    	"address": "서울시 강남구"
    }
    ```

- **응답**
  - **성공 응답**
    - 상태 코드: 200
    - 본문: 수정된 사용자 정보
    - 예시

      ```json
      {
      	"id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      	"email": "waffle@example.com",
      	"nickname": "와플이",
      	"address": "서울시 강남구",
      	"phone_number": "010-9876-5432"
      }
      ```

  - **실패 응답**

    | 상황                                           | 상태 코드 | ERROR_CODE | ERROR_MSG                |
    | ---------------------------------------------- | --------- | ---------- | ------------------------ |
    | 요청 필드가 비어있는 경우                      | 400       | ERR_002    | MISSING REQUIRED FIELDS  |
    | 요청 필드의 형식이 올바르지 않은 경우          | 400       | ERR_003    | INVALID FIELD FORMAT     |
    | Authorization 헤더가 제시되지 않은 경우        | 401       | ERR_005    | UNAUTHENTICATED          |
    | Authorization 헤더 값의 형식이 비정상적인 경우 | 400       | ERR_006    | BAD AUTHORIZATION HEADER |
    | 토큰이 유효하지 않은 경우                      | 401       | ERR_007    | INVALID TOKEN            |

##### 1-4) GET `/api/users/me/orders` — 내 주문 목록 조회 (로그인 필요)

- 로그인한 사용자의 모든 주문 목록을 조회합니다.

- **요청**
  - 헤더에 다음 필드가 포함됨

    ```
    Authorization: Bearer {access_token}
    ```

- **응답**
  - **성공 응답**
    - 상태 코드: 200
    - 본문: 주문 목록 배열
    - 예시

      ```json
      [
      	{
      		"order_id": "a0debb7b-5854-4afd-8bd4-80fdffa21410",
      		"total_price": 41000,
      		"status": "ORDERED"
      	},
      	{
      		"order_id": "b1f2cc8c-6965-5bge-9ce5-91geggb32521",
      		"total_price": 25000,
      		"status": "COMPLETE"
      	}
      ]
      ```

  - **실패 응답**

    | 상황                                           | 상태 코드 | ERROR_CODE | ERROR_MSG                |
    | ---------------------------------------------- | --------- | ---------- | ------------------------ |
    | Authorization 헤더가 제시되지 않은 경우        | 401       | ERR_005    | UNAUTHENTICATED          |
    | Authorization 헤더 값의 형식이 비정상적인 경우 | 400       | ERR_006    | BAD AUTHORIZATION HEADER |
    | 토큰이 유효하지 않은 경우                      | 401       | ERR_007    | INVALID TOKEN            |

#### 2. `/api/stores` 엔드포인트

##### 2-1) POST `/api/stores` — 상점 추가 (로그인 필요)

- 로그인한 사용자가 새로운 상점을 생성합니다. 한 사용자는 최대 하나의 상점만 소유할 수 있습니다.
- 상점 추가 요청이 들어오면 다음의 사항이 검증돼야 합니다.
  - 필요한 필드가 모두 있어야 합니다.
  - `store_name`: 3글자 이상 20글자 이하의 문자열이어야 합니다. 기존에 존재하는 상점과 중복되지 않는지 확인해야 합니다.
  - `address`: 100자 이하의 문자열이어야 합니다.
  - `email`: 이메일 형식이어야 합니다. 기존에 존재하는 상점과 중복되지 않는지 확인해야 합니다.
  - `phone_number`: 010-xxxx-xxxx 형식의 문자열이어야 합니다. 기존에 존재하는 상점과 중복되지 않는지 확인해야 합니다.
  - `delivery_fee`: 0 이상의 정수이어야 합니다.
  - 로그인한 유저가 이미 상점을 생성한 경우, 상점을 추가할 수 없습니다.
- 각 상점에는 고유 식별자로 `id`(str)가 부여됩니다.

- **요청**
  - 헤더에 다음 필드가 포함됨

    ```
    Authorization: Bearer {access_token}
    ```

  - 본문 예시

    ```json
    {
    	"store_name": "store1",
    	"address": "address1",
    	"email": "fastapi@wafflestudio.com",
    	"phone_number": "010-1234-5678",
    	"delivery_fee": 3000
    }
    ```

- **응답**
  - **성공 응답**
    - 상태 코드: 201
    - 본문: 생성된 상점 정보
    - 예시

      ```json
      {
      	"id": "6b5e1a9d-5f13-4cf0-b5f2-fde832c10534",
      	"store_name": "store1",
      	"address": "address1",
      	"email": "fastapi@wafflestudio.com",
      	"phone_number": "010-1234-5678",
      	"delivery_fee": 3000
      }
      ```

  - **실패 응답**

    | 상황                                           | 상태 코드 | ERROR_CODE | ERROR_MSG                |
    | ---------------------------------------------- | --------- | ---------- | ------------------------ |
    | 요청 필드가 비어있는 경우                      | 400       | ERR_002    | MISSING REQUIRED FIELDS  |
    | 요청 필드의 형식이 올바르지 않은 경우          | 400       | ERR_003    | INVALID FIELD FORMAT     |
    | Authorization 헤더가 제시되지 않은 경우        | 401       | ERR_005    | UNAUTHENTICATED          |
    | Authorization 헤더 값의 형식이 비정상적인 경우 | 400       | ERR_006    | BAD AUTHORIZATION HEADER |
    | 토큰이 유효하지 않은 경우                      | 401       | ERR_007    | INVALID TOKEN            |
    | 이미 상점을 소유하고 있는 경우                 | 409       | ERR_008    | STORE ALREADY EXISTS     |
    | 상점명/이메일/전화번호가 중복되는 경우         | 409       | ERR_009    | STORE INFO CONFLICT      |

##### 2-2) PATCH `/api/stores/{store_id}` — 상점 정보 수정 (로그인 필요)

- 상점 소유자가 자신의 상점 정보를 수정합니다.
- 상점 수정 요청이 들어오면 다음의 사항이 검증돼야 합니다.
  - 유저가 상점을 소유하고 있는지 확인해야 합니다.
  - 상점이 존재하는지 확인해야 합니다.
  - 유저가 소유한 상점인지 확인해야 합니다.
  - 요청 본문에 포함된 필드가 올바른지 확인해야 합니다. 또한 적어도 하나 이상의 필드가 포함되어야 합니다.
    - `store_name`: 3글자 이상 20글자 이하의 문자열이어야 합니다. 기존에 존재하는 상점과 중복되지 않는지 확인해야 합니다.
    - `address`: 100자 이하의 문자열이어야 합니다.
    - `email`: 이메일 형식이어야 합니다. 기존에 존재하는 상점과 중복되지 않는지 확인해야 합니다.
    - `phone_number`: 010-xxxx-xxxx 형식의 문자열이어야 합니다. 기존에 존재하는 상점과 중복되지 않는지 확인해야 합니다.
    - `delivery_fee`: 0 이상의 정수이어야 합니다.

- **요청**
  - 헤더에 다음 필드가 포함됨

    ```
    Authorization: Bearer {access_token}
    ```

  - URL 파라미터: `store_id` (str)
  - 본문 예시

    ```json
    {
    	"delivery_fee": 5000
    }
    ```

- **응답**
  - **성공 응답**
    - 상태 코드: 200
    - 본문: 수정된 상점 정보
    - 예시

      ```json
      {
      	"id": "6b5e1a9d-5f13-4cf0-b5f2-fde832c10534",
      	"store_name": "store1",
      	"address": "address1",
      	"email": "fastapi@wafflestudio.com",
      	"phone_number": "010-1234-5678",
      	"delivery_fee": 5000
      }
      ```

  - **실패 응답**

    | 상황                                           | 상태 코드 | ERROR_CODE | ERROR_MSG                |
    | ---------------------------------------------- | --------- | ---------- | ------------------------ |
    | 요청 필드가 비어있는 경우                      | 400       | ERR_002    | MISSING REQUIRED FIELDS  |
    | 요청 필드의 형식이 올바르지 않은 경우          | 400       | ERR_003    | INVALID FIELD FORMAT     |
    | Authorization 헤더가 제시되지 않은 경우        | 401       | ERR_005    | UNAUTHENTICATED          |
    | Authorization 헤더 값의 형식이 비정상적인 경우 | 400       | ERR_006    | BAD AUTHORIZATION HEADER |
    | 토큰이 유효하지 않은 경우                      | 401       | ERR_007    | INVALID TOKEN            |
    | 상점명/이메일/전화번호가 중복되는 경우         | 409       | ERR_009    | STORE INFO CONFLICT      |
    | 상점이 존재하지 않는 경우                      | 404       | ERR_010    | STORE NOT FOUND          |
    | 상점을 소유하지 않은 경우                      | 403       | ERR_011    | NO STORE OWNED           |
    | 다른 상점을 수정하려는 경우                    | 403       | ERR_012    | NOT YOUR STORE           |

##### 2-3) GET `/api/stores/{store_id}` — 상점 조회

- 지정된 ID의 상점 정보를 조회합니다.
- 상점 조회 요청이 들어오면 다음의 사항이 검증돼야 합니다.
  - 상점이 존재하는지 확인해야 합니다.

- **요청**
  - URL 파라미터: `store_id` (str)

- **응답**
  - **성공 응답**
    - 상태 코드: 200
    - 본문: 상점 정보
    - 예시

      ```json
      {
      	"id": "6b5e1a9d-5f13-4cf0-b5f2-fde832c10534",
      	"store_name": "store1",
      	"address": "address1",
      	"email": "fastapi@wafflestudio.com",
      	"phone_number": "010-1234-5678",
      	"delivery_fee": 3000
      }
      ```

  - **실패 응답**

    | 상황                      | 상태 코드 | ERROR_CODE | ERROR_MSG       |
    | ------------------------- | --------- | ---------- | --------------- |
    | 상점이 존재하지 않는 경우 | 404       | ERR_010    | STORE NOT FOUND |

##### 2-4) GET `/api/stores/{store_id}/items` — 상점의 상품 목록 조회

- 특정 상점의 모든 상품을 조회합니다.

- **요청**
  - URL 파라미터: `store_id` (문자열)

- **응답**
  - **성공 응답**
    - 상태 코드: 200
    - 본문: 상품 목록 배열
    - 예시

      ```json
      [
      	{
      		"id": "6b5e1a9d-5f13-4cf0-b5f2-fde832c10534",
      		"item_name": "와플",
          "price": 10000,
      		"stock": 15
      	},
      	{
      		"id": "a58a2711-9f60-42ea-89ed-ad91942b790a",
      		"item_name": "시럽",
      		"price": 3000,
      		"stock": 8
      	}
      ]
      ```

  - **실패 응답**

    | 상황                      | 상태 코드 | ERROR_CODE | ERROR_MSG       |
    | ------------------------- | --------- | ---------- | --------------- |
    | 상점이 존재하지 않는 경우 | 404       | ERR_010    | STORE NOT FOUND |

#### 3. `/api/items` 엔드포인트

##### 3-1) POST `/api/items` — 상품 추가 (로그인 필요)

- 상점 소유자가 자신의 상점에 새로운 상품을 추가합니다.
- 상품 추가 요청이 들어오면 다음의 사항이 검증돼야 합니다.
  - 유저가 상점을 소유하고 있는지 확인해야 합니다.
  - 필요한 필드가 모두 있어야 합니다.
  - `item_name`: 2글자 이상 50글자 이하의 문자열이어야 합니다.
  - `price`: 0 이상의 정수이어야 합니다.
  - `stock`: 0 이상의 정수이어야 합니다.
- 각 상품에는 고유 식별자로 `id`(str)가 부여됩니다.

- **요청**
  - 헤더에 다음 필드가 포함됨

    ```
    Authorization: Bearer {access_token}
    ```

  - 본문 예시

    ```json
    {
    	"item_name": "item1",
    	"price": 10000,
    	"stock": 10
    }
    ```

- **응답**
  - **성공 응답**
    - 상태 코드: 201
    - 본문: 생성된 상품 정보
    - 예시

      ```json
      {
      	"id": "6b5e1a9d-5f13-4cf0-b5f2-fde832c10534",
      	"item_name": "item1",
      	"price": 10000,
      	"stock": 10
      }
      ```

  - **실패 응답**

    | 상황                                           | 상태 코드 | ERROR_CODE | ERROR_MSG                |
    | ---------------------------------------------- | --------- | ---------- | ------------------------ |
    | 요청 필드가 비어있는 경우                      | 400       | ERR_002    | MISSING REQUIRED FIELDS  |
    | 요청 필드의 형식이 올바르지 않은 경우          | 400       | ERR_003    | INVALID FIELD FORMAT     |
    | Authorization 헤더가 제시되지 않은 경우        | 401       | ERR_005    | UNAUTHENTICATED          |
    | Authorization 헤더 값의 형식이 비정상적인 경우 | 400       | ERR_006    | BAD AUTHORIZATION HEADER |
    | 토큰이 유효하지 않은 경우                      | 401       | ERR_007    | INVALID TOKEN            |
    | 상점을 소유하지 않은 경우                      | 403       | ERR_011    | NO STORE OWNED           |

##### 3-2) PATCH `/api/items/{item_id}` — 상품 수정 (로그인 필요)

- 상점 소유자가 자신의 상점에 속한 상품의 정보를 수정합니다.
- 상품 수정 요청이 들어오면 다음의 사항이 검증돼야 합니다.
  - 유저가 상점을 소유하고 있는지 확인해야 합니다.
  - 상품이 존재하는지 확인해야 합니다.
  - 유저가 소유한 상점의 상품인지 확인해야 합니다.
  - 요청 본문에 포함된 필드가 올바른지 확인해야 합니다. 또한 적어도 하나 이상의 필드가 포함되어야 합니다.
    - `item_name`: 2글자 이상 50글자 이하의 문자열이어야 합니다.
    - `price`: 0 이상의 정수이어야 합니다.
    - `stock`: 0 이상의 정수이어야 합니다.

- **요청**
  - 헤더에 다음 필드가 포함됨

    ```
    Authorization: Bearer {access_token}
    ```

  - URL 파라미터: `item_id` (str)
  - 본문 예시

    ```json
    {
    	"item_name": "item1",
    	"price": 15000,
    	"stock": 10
    }
    ```

- **응답**
  - **성공 응답**
    - 상태 코드: 200
    - 본문: 수정된 상품 정보
    - 예시

      ```json
      {
      	"id": "6b5e1a9d-5f13-4cf0-b5f2-fde832c10534",
      	"item_name": "item1",
      	"price": 15000,
      	"stock": 10
      }
      ```

  - **실패 응답**

    | 상황                                           | 상태 코드 | ERROR_CODE | ERROR_MSG                |
    | ---------------------------------------------- | --------- | ---------- | ------------------------ |
    | 요청 필드가 비어있는 경우                      | 400       | ERR_002    | MISSING REQUIRED FIELDS  |
    | 요청 필드의 형식이 올바르지 않은 경우          | 400       | ERR_003    | INVALID FIELD FORMAT     |
    | Authorization 헤더가 제시되지 않은 경우        | 401       | ERR_005    | UNAUTHENTICATED          |
    | Authorization 헤더 값의 형식이 비정상적인 경우 | 400       | ERR_006    | BAD AUTHORIZATION HEADER |
    | 토큰이 유효하지 않은 경우                      | 401       | ERR_007    | INVALID TOKEN            |
    | 상점을 소유하지 않은 경우                      | 403       | ERR_011    | NO STORE OWNED           |
    | 상품이 존재하지 않는 경우                      | 404       | ERR_013    | ITEM NOT FOUND           |
    | 다른 상점의 상품을 수정하려는 경우             | 403       | ERR_014    | NOT YOUR ITEM            |

##### 3-3) GET `/api/items` — 상품 목록 조회

- 전체 상품 목록을 조회하며, 쿼리 파라미터를 통해 필터링이 가능합니다.
- 쿼리 파라미터를 이용해 다음과 같이 필터링해야 합니다.
  - `store_id`: 특정 상점의 상품만 조회할 때 사용합니다.
  - `min_price`: 지정된 최소 가격 이상의 상품을 조회할 때 사용합니다.
  - `max_price`: 지정된 최대 가격 이하의 상품을 조회할 때 사용합니다.
  - `in_stock`: 재고가 있는 상품만 조회할 때 사용합니다.
    - `true`로 설정할 경우, 재고가 있는 상품만 조회합니다.
    - `false`로 설정할 경우, 모든 상품을 조회합니다.
    - 기본값은 `false`입니다.
  - 모든 조건은 AND 조건입니다.

- **요청**
  - 쿼리 파라미터 (선택사항)
    - `store_id`: 상점 ID (문자열)
    - `min_price`: 최소 가격 (정수)
    - `max_price`: 최대 가격 (정수)
    - `in_stock`: 재고 여부 (boolean, 기본값: false)

- **응답**
  - **성공 응답**
    - 상태 코드: 200
    - 본문: 상품 목록 배열
    - 예시

      ```json
      [
      	{
      		"id": "6b5e1a9d-5f13-4cf0-b5f2-fde832c10534",
      		"item_name": "item1",
      		"price": 15000,
      		"stock": 10,
      		"store_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      		"store_name": "와플 스토어"
      	},
      	{
      		"id": "a58a2711-9f60-42ea-89ed-ad91942b790a",
      		"item_name": "item2",
      		"price": 20000,
      		"stock": 5,
      		"store_id": "b8e7f3a2-1c4d-5e6f-9012-345678901234",
      		"store_name": "초콜릿 스토어"
      	}
      ]
      ```

  - **실패 응답**

    | 상황                             | 상태 코드 | ERROR_CODE | ERROR_MSG       |
    | -------------------------------- | --------- | ---------- | --------------- |
    | 지정된 상점이 존재하지 않는 경우 | 404       | ERR_010    | STORE NOT FOUND |

##### 3-4) DELETE `/api/items/{item_id}` — 상품 삭제 (로그인 필요)

- 로그인한 사용자가 자신의 상점의 상품을 삭제합니다. 재고를 0으로 만드는 것과 달리 상품을 완전히 삭제하여 목록에서 제거합니다.
- 상품 삭제 요청이 들어오면 다음의 사항이 검증돼야 합니다.
  - 상품이 존재하는지 확인해야 합니다.
  - 로그인한 사용자가 해당 상품의 상점 소유자인지 확인해야 합니다.

- **요청**
  - 헤더에 다음 필드가 포함됨

    ```
    Authorization: Bearer {access_token}
    ```

  - URL 파라미터: `item_id` (문자열)

- **응답**
  - **성공 응답**
    - 상태 코드: 204
    - 본문: 없음

  - **실패 응답**

    | 상황                                           | 상태 코드 | ERROR_CODE | ERROR_MSG                |
    | ---------------------------------------------- | --------- | ---------- | ------------------------ |
    | Authorization 헤더가 제시되지 않은 경우        | 401       | ERR_005    | UNAUTHENTICATED          |
    | Authorization 헤더 값의 형식이 비정상적인 경우 | 400       | ERR_006    | BAD AUTHORIZATION HEADER |
    | 토큰이 유효하지 않은 경우                      | 401       | ERR_007    | INVALID TOKEN            |
    | 상품이 존재하지 않는 경우                      | 404       | ERR_013    | ITEM NOT FOUND           |
    | 상품의 소유자가 아닌 경우                      | 403       | ERR_014    | NOT YOUR ITEM            |

#### 4. `/api/orders` 엔드포인트

##### 4-1) POST `/api/orders` — 주문 생성 (로그인 필요)

- 로그인한 사용자가 여러 상품을 주문합니다. 주문 시 각 상품의 재고가 주문 수량만큼 감소합니다.
- 주문 생성과 재고 차감은 하나의 트랜잭션으로 처리합니다. 요청이 실패하면 주문을 저장하지 않고, 모든 상품의 재고를 요청 전 상태로 유지합니다.
- 주문 생성 요청 시 다음의 사항이 검증돼야 합니다.
  - `items` 필드를 포함해야 합니다.
    - `items` 필드는 `item_id`와 `quantity`를 포함하는 배열이어야 합니다.
    - 같은 `item_id`를 두 번 이상 포함하면 요청을 거절합니다. 수량을 합산하지 않으며, `400 / ERR_003 / INVALID FIELD FORMAT`을 반환합니다.
  - 수량은 1 이상의 정수이어야 합니다.
  - 각 상품이 존재하는지 확인해야 합니다.
  - 주문 수량이 재고보다 많지 않은지 확인해야 합니다.
- 각 주문에는 고유 식별자로 `id`(str)가 부여됩니다.

- **요청**
  - 헤더에 다음 필드가 포함됨

    ```
    Authorization: Bearer {access_token}
    ```

  - 본문 예시

    ```json
    {
    	"items": [
    		{
    			"item_id": "4a40d8f9-6d90-4189-8f93-de0d4a89d6cf",
    			"quantity": 2
    		},
    		{
    			"item_id": "789c1422-9063-46b9-b999-8bf4a4f8e28d",
    			"quantity": 1
    		}
    	]
    }
    ```

- **응답**
  - **성공 응답**
    - 상태 코드: 201
    - 본문: 생성된 주문 정보
    - 예시

      ```json
      {
      	"order_id": "a0debb7b-5854-4afd-8bd4-80fdffa21410",
      	"details": [
      		{
      			"store_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      			"store_name": "와플 스토어",
      			"delivery_fee": 3000,
      			"store_total_price": 23000,
      			"items": [
      				{
      					"item_id": "4a40d8f9-6d90-4189-8f93-de0d4a89d6cf",
      					"item_name": "와플",
      					"price": 10000,
      					"quantity": 2,
      					"subtotal": 20000
      				}
      			]
      		},
      		{
      			"store_id": "b8e7f3a2-1c4d-5e6f-9012-345678901234",
      			"store_name": "초콜릿 스토어",
      			"delivery_fee": 2500,
      			"store_total_price": 17500,
      			"items": [
      				{
      					"item_id": "789c1422-9063-46b9-b999-8bf4a4f8e28d",
      					"item_name": "초콜릿",
      					"price": 15000,
      					"quantity": 1,
      					"subtotal": 15000
      				}
      			]
      		}
      	],
      	"total_price": 40500,
      	"status": "ORDERED"
      }
      ```

  - **실패 응답**

    | 상황                                           | 상태 코드 | ERROR_CODE | ERROR_MSG                |
    | ---------------------------------------------- | --------- | ---------- | ------------------------ |
    | 요청 필드가 비어있는 경우                      | 400       | ERR_002    | MISSING REQUIRED FIELDS  |
    | 요청 필드의 형식이 올바르지 않은 경우          | 400       | ERR_003    | INVALID FIELD FORMAT     |
    | Authorization 헤더가 제시되지 않은 경우        | 401       | ERR_005    | UNAUTHENTICATED          |
    | Authorization 헤더 값의 형식이 비정상적인 경우 | 400       | ERR_006    | BAD AUTHORIZATION HEADER |
    | 토큰이 유효하지 않은 경우                      | 401       | ERR_007    | INVALID TOKEN            |
    | 상품이 존재하지 않는 경우                      | 404       | ERR_013    | ITEM NOT FOUND           |
    | 재고가 부족한 경우                             | 409       | ERR_017    | NOT ENOUGH STOCK         |
    | items가 빈 배열인 경우                         | 422       | ERR_018    | EMPTY ITEM LIST          |

##### 4-2) GET `/api/orders/{order_id}` — 주문 조회 (로그인 필요)

- 로그인한 사용자가 자신의 주문 정보를 조회합니다.
- 주문 조회 요청이 들어오면 다음의 사항이 검증돼야 합니다.
  - 주문이 존재하는지 확인해야 합니다.
  - 해당 주문이 로그인한 유저의 주문인지 확인해야 합니다.

- **요청**
  - 헤더에 다음 필드가 포함됨

    ```
    Authorization: Bearer {access_token}
    ```

  - URL 파라미터: `order_id` (str)

- **응답**
  - **성공 응답**
    - 상태 코드: 200
    - 본문: 주문 정보
    - 예시

      ```json
      {
      	"order_id": "a0debb7b-5854-4afd-8bd4-80fdffa21410",
      	"details": [
      		{
      			"store_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      			"store_name": "와플 스토어",
      			"delivery_fee": 3000,
      			"store_total_price": 23000,
      			"items": [
      				{
      					"item_id": "4a40d8f9-6d90-4189-8f93-de0d4a89d6cf",
      					"item_name": "와플",
      					"price": 10000,
      					"quantity": 2,
      					"subtotal": 20000
      				}
      			]
      		},
      		{
      			"store_id": "b8e7f3a2-1c4d-5e6f-9012-345678901234",
      			"store_name": "초콜릿 스토어",
      			"delivery_fee": 2500,
      			"store_total_price": 17500,
      			"items": [
      				{
      					"item_id": "789c1422-9063-46b9-b999-8bf4a4f8e28d",
      					"item_name": "초콜릿",
      					"price": 15000,
      					"quantity": 1,
      					"subtotal": 15000
      				}
      			]
      		}
      	],
      	"total_price": 40500,
      	"status": "ORDERED"
      }
      ```

  - **실패 응답**

    | 상황                                           | 상태 코드 | ERROR_CODE | ERROR_MSG                |
    | ---------------------------------------------- | --------- | ---------- | ------------------------ |
    | Authorization 헤더가 제시되지 않은 경우        | 401       | ERR_005    | UNAUTHENTICATED          |
    | Authorization 헤더 값의 형식이 비정상적인 경우 | 400       | ERR_006    | BAD AUTHORIZATION HEADER |
    | 토큰이 유효하지 않은 경우                      | 401       | ERR_007    | INVALID TOKEN            |
    | 주문이 존재하지 않는 경우                      | 404       | ERR_019    | ORDER NOT FOUND          |
    | 다른 유저의 주문을 조회하려고 할 경우          | 403       | ERR_020    | NOT YOUR ORDER           |

##### 4-3) PATCH `/api/orders/{order_id}` — 주문 상태 변경 (로그인 필요)

- 로그인한 사용자가 자신의 주문 상태를 변경합니다. 주문 취소 또는 구매 확정이 가능합니다.
- 주문 상태 변경 요청이 들어오면 다음의 사항이 검증돼야 합니다.
  - 필요한 필드가 모두 있어야 합니다.
  - `status`: `CANCELED` 또는 `COMPLETE` 중 하나여야 합니다.
  - 주문이 존재하는지 확인해야 합니다.
  - 해당 주문이 로그인한 유저의 주문인지 확인해야 합니다.
  - 주문의 현재 상태가 `ORDERED`인지 확인해야 합니다. (이미 취소되었거나, 구매 확정된 주문은 변경할 수 없습니다.)

- **요청**
  - 헤더에 다음 필드가 포함됨

    ```
    Authorization: Bearer {access_token}
    ```

  - URL 파라미터: `order_id` (문자열)
  - 본문 예시 (주문 취소)

    ```json
    {
    	"status": "CANCELED"
    }
    ```

  - 본문 예시 (구매 확정)

    ```json
    {
    	"status": "COMPLETE"
    }
    ```

- **응답**
  - **성공 응답**
    - 상태 코드: 204
    - 본문: 없음

  - **실패 응답**

    | 상황                                               | 상태 코드 | ERROR_CODE | ERROR_MSG                |
    | -------------------------------------------------- | --------- | ---------- | ------------------------ |
    | 요청 필드가 비어있는 경우                          | 400       | ERR_002    | MISSING REQUIRED FIELDS  |
    | 요청 필드의 형식이 올바르지 않은 경우              | 400       | ERR_003    | INVALID FIELD FORMAT     |
    | Authorization 헤더가 제시되지 않은 경우            | 401       | ERR_005    | UNAUTHENTICATED          |
    | Authorization 헤더 값의 형식이 비정상적인 경우     | 400       | ERR_006    | BAD AUTHORIZATION HEADER |
    | 토큰이 유효하지 않은 경우                          | 401       | ERR_007    | INVALID TOKEN            |
    | 주문이 존재하지 않는 경우                          | 404       | ERR_019    | ORDER NOT FOUND          |
    | 이미 취소되었거나 완료된 주문을 변경하려고 할 경우 | 409       | ERR_021    | INVALID ORDER STATUS     |
    | 다른 유저의 주문을 변경하려고 할 경우              | 403       | ERR_020    | NOT YOUR ORDER           |

### 4. EC2·RDS 및 CI/CD

#### EC2 배포와 자동 배포(CD)

- API 서버를 EC2에서 실행하고, 제출한 주소로 채점자가 API에 접근할 수 있어야 합니다.
- 저장소 루트의 `ip.py` 파일에서 `EC2_IP`에 EC2 퍼블릭 IPv4 주소를 작성해주세요. 해당 주소의 `/health` 응답에 포함된 소스 해시를 비교하여 제출한 코드와 동일한 코드가 배포되었는지 확인합니다.
- `main`에 반영된 변경은 해당 커밋의 CI 테스트를 통과한 뒤 EC2에 자동 배포되어야 합니다. 테스트 실패 시 배포되면 안 됩니다.
- CD는 `.github/workflows/cd.yaml`의 **빈 파일**만 제공합니다. 이 파일에 트리거, 테스트(5회차 세미나 이후), 배포 작업을 작성해야 합니다. 빈 파일은 완성된 워크플로우가 아니며, 구현 전에는 배포가 실행되지 않습니다.
- 배포 시 필요한 Alembic 마이그레이션을 적용하고, 배포 후 API가 정상 동작하는지 확인합니다.

#### CI 테스트 (5주차 세미나 이후)

- `.github/workflows/ci.yaml`에 제공된 테스트 워크플로우를 사용합니다. PR과 `main` 푸시에서 `ENV=test uv run pytest`를 실행합니다.
- CI용 데이터베이스는 기존 메모리 SQLite를 사용합니다. CI에 RDS 접속 정보를 넣을 필요는 없습니다.
- 모든 엔드포인트에 대해 API 테스트를 작성합니다. 성공한 경우(2xx)에 대한 테스트와, 실패한 경우(4xx)에 대한 테스트 전부 작성해야 합니다.

#### DB

- EC2의 API 서버는 AWS RDS MySQL 또는 OCI HeatWave를 사용해야 합니다. 로컬 DB 또는 EC2 내부 DB만 사용한 배포는 완료로 인정하지 않습니다.
- RDS에 Alembic 마이그레이션을 적용하고, EC2의 API를 통해 회원·상점·상품·주문 데이터가 저장·조회되는지 확인합니다.
- RDS의 DB 포트 접근은 EC2 보안 그룹 등 필요한 출처로 제한합니다. DB 비밀번호·SSH 개인키·인증 키를 저장소에 올리지 않습니다.
