# meta-sejong-project_5team
메타버스인공지능기술 프로젝트


# MetaSejong DB v1
DB 초기 버전

구성
- meta_sejong_v1_schema.sql : 데이터베이스 테이블 및 제약조건 정의
- meta_sejong_v1_seed.sql : 초기 데이터 삽입 (식당, 메뉴, 노드, 엣지 등)

주요 내용
- 복도 기반 A* / Dijkstra 탐색 가능한 nodes & edges 구조
- 충무관, 다산관, 영실관, 주차장, 초등학교홀의 실제 좌표 반영
- 모든 건물 간 이동 경로 검증 완료
- 식당 4곳 (나루또, 아지오, 반미하우스, 스시고) 및 메뉴 정보 포함

실행
```bash
mysql -u root -p < schema/meta_sejong_v1_schema.sql
mysql -u root -p metasejong < schema/meta_sejong_v1_seed.sql
