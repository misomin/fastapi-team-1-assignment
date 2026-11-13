# EC2 자동 배포

아래는 과제 요구사항을 구현하기 위해 추가한 배포 방식입니다. 서버는 Ubuntu 24.04의
`ubuntu` 사용자, Python 3.12, `/home/ubuntu/.local/bin/uv`를 기준으로 합니다.
모델과 API 코드를 바꾸지 않고 기존 Alembic revision을 사용합니다.

- 기존 `CI`의 **같은 저장소 main push** 실행이 성공한 경우에만 `CD`가 시작합니다.
- CI가 검사한 `workflow_run.head_sha`를 checkout하고 그 커밋을 `git archive`로 전송합니다.
  EC2에서 main을 다시 pull하지 않습니다. 환경 파일과 Git 인증 정보는 전송하지 않습니다.
- 전송 전에 현재 main과 SHA를 두 번 비교해 오래된 CI 결과를 건너뜁니다.
- GitHub concurrency는 진행 중인 배포를 취소하지 않습니다. EC2의 `flock`도 migration부터
  배포 확인까지 잠급니다. EC2는 마지막 시도의 **CI 실행 번호**보다 오래된 실행을 거부합니다.
  실패한 migration이 일부 반영됐을 수도 있으므로 마지막 성공뿐 아니라 시도도 기록합니다.
- GitHub Actions 설정상 CD 파일은 기본 브랜치에 반영되어야 동작합니다.

## 실제 배포 전 준비

### 2026-11-13 운영 대상 확인

- 기존 `seminar` 대신 사용자가 별도로 생성한 `wapang` DB를 사용합니다.
- EC2에서 RDS `database-1`의 MySQL 8.4.11에 운영 설정으로 인증하고 `SELECT 1`을 확인했습니다.
  `wapang`의 문자셋은 `utf8mb4`, collation은 `utf8mb4_0900_ai_ci`이며,
  점검 당시 테이블과 `alembic_version`은 없었습니다. 실제 배포 직전에 다시 확인합니다.
- `/home/ubuntu/wapang/shared/production.env`를 권한 `600`으로 준비했습니다.
  비밀번호는 사용자가 EC2에서 직접 입력했고, 토큰 서명 키는 서버에서 생성했습니다.
  실제 값은 저장소나 채팅에 포함하지 않습니다.
- 연결 검사는 별도 `preflight.*` 디렉터리에서 실행했습니다. 이 작업으로 migration이나
  systemd 설치·서비스 중지는 실행하지 않았으며, 실제 migration과 배포에는 별도 요청이 필요합니다.
- 로컬 AWS CLI의 `wapang` 프로필은 서울 리전에서 `user/wapang-inspect`로 인증했고,
  STS로 계정과 사용자를 확인했습니다. 로그인 세션은 만료될 수 있습니다.
- GitHub 저장소에 `EC2_HOST=15.164.230.226`, `EC2_USER=ubuntu` Variables와
  `EC2_KNOWN_HOSTS` Secret을 등록했습니다. 호스트 키는 기존 `known_hosts` 및
  인증된 SSH 연결에서 읽은 서버 공개키와 대조했습니다.
  `EC2_SSH_PRIVATE_KEY`도 사용자 승인 후 등록하고 Secret 이름·등록 시각을 확인했습니다.
  Secrets의 실제 값은 출력하지 않았으며, CD 실행으로 해당 값을 사용하는 검증은 아직 하지 않았습니다.

### 준비 절차

이 절차는 실제 서버 설정·배포를 승인받은 뒤 수행합니다. 파일을 작성하는 것만으로
배포나 RDS migration이 실행되지는 않습니다.

1. EC2에서 사용할 RDS의 DB 이름과 계정 권한을 확인합니다. `DBName`이 비어 있다는
   AWS 조회 결과만으로 실제 스키마가 없다고 판단하지 않습니다. Alembic은 DB 내부의
   테이블을 생성하며 MySQL 데이터베이스 자체를 생성하지 않습니다.
2. `/home/ubuntu/wapang/shared`를 `ubuntu` 소유, 권한 `700`으로 준비합니다.
   `deploy/production.env.example`을 참고해 `production.env`를 작성하고 권한을 `600`으로
   설정합니다. 실제 값은 EC2에만 저장하며 `.env.test`와 저장소의 예시 파일은 수정하지 않습니다.
   이미 파일이 있다면 덮어쓰지 말고 기존 설정부터 확인합니다.
3. 앱과 Alembic 모두 같은 `shared/production.env`를 `uv run --env-file`로 읽습니다.
   `ENV=prod`는 배포 스크립트와 systemd에서 고정하고, 로그인 셸의 DB·인증 변수는 제거해
   예기치 않은 환경변수 덮어쓰기를 방지합니다. 파일은 dotenv 형식으로 작성하며
   `export`, 셸 명령, 변수 참조 대신 실제 값을 사용합니다. 공백·`#` 등이 있는 값은 따옴표로 감쌉니다.
4. `ubuntu`의 비대화형 sudo가 Docker 조회·기존 컨테이너 중지·unit 설치·systemctl 실행에
   사용할 수 있는지 확인합니다. 서비스 자체는 `ubuntu`로 실행하고 80번 바인딩에 필요한
   capability만 systemd에서 부여합니다.
5. 저장소 **Settings → Secrets and variables → Actions**에 다음을 설정합니다.

| 종류 | 이름 | 내용 |
| --- | --- | --- |
| Variable | `EC2_HOST` | 대상 EC2의 퍼블릭 IPv4 또는 DNS |
| Variable | `EC2_USER` | `ubuntu` |
| Secret | `EC2_SSH_PRIVATE_KEY` | 대상 서버에 접속할 SSH 개인키 |
| Secret | `EC2_KNOWN_HOSTS` | 신뢰할 수 있는 경로에서 확인한 해당 호스트의 known_hosts 항목 |

호스트 키는 서버와 대조해 등록합니다. CD에서 `ssh-keyscan` 결과를 자동 신뢰하거나
호스트 키 검증을 끄지 않습니다. GitHub Actions에는 RDS 비밀번호를 등록할 필요가 없습니다.
EC2는 소스 묶음을 전달받으므로 비공개 저장소의 clone용 자격증명도 필요하지 않습니다.

## 배포 순서와 실패 처리

```text
CI 성공 및 SHA 확인 → 코드 전송 → EC2 잠금/실행 번호 확인
→ 별도 release 디렉터리에 uv sync --frozen --python 3.12
→ 운영 DB 인증 및 SELECT 1 → systemd 설정 설치
→ 기존 wapang 서비스 중지 → 기존 과제 3 컨테이너의 자동 재시작 해제·중지
→ alembic upgrade head → current 링크 전환 → 서비스 재시작
→ 로컬 /health 소스 해시 및 DB 재확인 → 외부 /health 소스 해시 확인
```

- `deploy/deploy.sh`는 CD에서 호출하는 배포 실행 코드입니다. 모델 변경이나 revision 생성은
  수행하지 않습니다. 운영 DB 인증 검사는 `deploy/check_database.py`가 담당합니다.
- 의존성 설치·DB 검사 실패 시 기존 서비스를 유지합니다. 과제 제출용 서비스이므로
  배포 중 중단을 허용하고, 기존 앱을 중지한 후 migration을 실행합니다.
  이전 코드와 새 스키마 사이의 호환성은 요구하지 않습니다.
- migration 실패 시 앱은 중지 상태로 남고 current 링크 전환·서비스 재시작을 수행하지 않습니다.
  재시작·health 검증이 실패해도 CD는 실패 처리하며 자동 DB downgrade나 코드 롤백을 하지 않습니다.
  MySQL DDL은 트랜잭션 rollback으로 모두 복구되지 않을 수 있으므로 실패 원인을 확인한 뒤 재시도합니다.
- 이미 사용하지 않기로 한 `fastapi-assignment-3` 컨테이너만 대상으로 하며, 다른 컨테이너와
  데이터는 삭제하지 않습니다. 최초 실제 배포 전까지 기존 서비스는 그대로 실행됩니다.
- `/health`의 `hash`는 Git SHA가 아니라 `wapang`의 Python 소스로 계산한 해시입니다.
  CD는 대상 커밋에서 같은 함수를 실행해 비교합니다. `/health`만으로 RDS 연결을 판단하지 않습니다.
- `last-attempt`에는 CI 실행 번호·커밋이, 로컬 배포 확인이 끝난 `last-deployed`에는 소스 해시도
  기록됩니다. 외부 접근 확인이 실패한 경우에는 로컬 기록이 있어도 CD 전체는 실패입니다.
  같은 CI 실행을 재시도할 수 있으며, 더 오래된 커밋으로 돌아가려면 main에 revert를 반영하고
  새 CI를 통과시킵니다. release 디렉터리와 실패한 시도는 자동 삭제하지 않습니다.

## 배포 후 확인

```bash
sudo systemctl status wapang.service
cat /home/ubuntu/wapang/last-deployed
```

GitHub의 외부 health 검사까지 통과한 뒤 `ip.py`의 주소와 배포 소스 해시를 확인합니다.
전체 API가 완성되면 EC2 API로 회원·상점·상품·주문이 RDS에 저장·조회되는지 별도로 검증합니다.
로컬의 배포 실패 경로 검증은 `ENV=test uv run pytest tests/deploy`로 실행할 수 있습니다.

## 로컬 검증 결과 (2026-11-13)

- `ENV=test uv run --frozen --python 3.12 pytest`: Python 3.12.14에서 48개 통과.
  이 중 `tests/deploy`의 13개 검사는 임시 디렉터리와 명령 대역을 사용해 사전 검사 실패 시
  기존 서비스 유지, migration 실패 시 재시작 차단, 중지·migration·재시작 순서,
  health 실패 시 성공 기록 방지, 오래된 실행 거부, 동일 실행 재시도와 SHA 변경 거부,
  배포 잠금, health 해시 검사 및 설정 오류 시 비밀 값 비노출을 검증합니다.
- `actionlint .github/workflows/ci.yaml .github/workflows/cd.yaml`: v1.7.12에서 통과.
- `bash -n deploy/deploy.sh`와 `git diff --check`: 통과.
- `ENV=test uv run --frozen --python 3.12 alembic heads`: 단일 head `8da7c4b3f9fd` 확인.
  새 revision은 생성하지 않았습니다.
- 루트 `README.md`와 `.env.test`는 기준 main `069dca7` 대비 변경이 없습니다.

위 pytest의 DB fixture는 메모리 SQLite를 사용합니다. 이 실행은 MySQL migration 재검증이나
실제 systemd·Docker·GitHub Actions 실행을 포함하지 않습니다. CI 성공 SHA 선택 조건은
workflow 코드 검토와 문법 검사로 확인했으며, 실제 CI/CD 연동과 RDS migration·배포는
별도 요청 후 검증해야 합니다. 전체 API 구현 완료를 의미하지 않습니다.
