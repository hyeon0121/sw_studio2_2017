# sw2 프로젝트 

docker를 이용하여 MySQL, Arcus, nBase-ARC, nGrinder를 사용하여 성능을 비교했습니다.

## Installation Guide

1. docker 이미지 pull 
```bash
docker pull ruo91/arcus
```
2. HostOS에서 Arcus Admin과 Memcached로 사용될 Container의 이미지를 생성
- Arcus admin
```bash
docker run -d --name="arcus-admin" -h "arcus" ruo91/arcus
```
- Memcached
```bash
docker run -d --name="arcus-memcached-1" -h "memcached-1" ruo91/arcus:memcached
docker run -d --name="arcus-memcached-2" -h "memcached-2" ruo91/arcus:memcached
docker run -d --name="arcus-memcached-3" -h "memcached-3" ruo91/arcus:memcached
```
3. 1 Zookeeper 설정
```bash
root@arcus:/opt/arcus/scripts# sed -i 's/127.0.0.1:2181/172.17.0.3:2181,172.17.0.4:2181,172.17.0.5:2181/g' arcus.sh
```
3. 2 SSH Public Key 생성 및 배포
```bash
root@arcus:/opt/arcus/scripts# ssh-keygen -t dsa -P '' -f "/root/.ssh/id_dsa"
root@arcus:/opt/arcus/scripts# cat /root/.ssh/id_dsa.pub >> /root/.ssh/authorized_keys
root@arcus:/opt/arcus/scripts# chmod 644 /root/.ssh/authorized_keys
root@arcus:/opt/arcus/scripts# scp /root/.ssh/authorized_keys root@172.17.0.3:/root/.ssh
root@arcus:/opt/arcus/scripts# scp /root/.ssh/authorized_keys root@172.17.0.4:/root/.ssh
root@arcus:/opt/arcus/scripts# scp /root/.ssh/authorized_keys root@172.17.0.5:/root/.ssh

```
3. 3 캐시 클라우드 설정
```bash
root@arcus:/opt/arcus/scripts# nano conf/ruo91.json
```
4. Arcus 배포
memcached-1, memcached-2, memcached-3 서버에 arcus를 배포합니다 .
```bash
root@arcus:/opt/arcus/scripts# ./arcus.sh deploy conf/ruo91.json
```
5. Zookeeper 앙상블 설정 및 실행
```bash
root@arcus:/opt/arcus/scripts# ./arcus.sh zookeeper init
root@arcus:/opt/arcus/scripts# ./arcus.sh zookeeper start
```
6. Memcached 등록 및 실행
```bash
root@arcus:/opt/arcus/scripts# ./arcus.sh memcached register conf/ruo91.json
root@arcus:/opt/arcus/scripts# ./arcus.sh memcached start ruo91-cloud
```
7. docker 에서 arcus-admin, Arcus-memcached-1 ,Arcus-memcached-2, Arcus-memcached-3 순서대로 켜줍니다.
8. docker network inspect bridge 해서 ip 맞춰주고 Database 이름과 build 한 이름을  맞춰주면 됩니다.

## 프로젝트 MySQL
askhy_mysql 폴더에서 진행합니다.

MySQL 컨테이너가 없다면 다음 명령어를 먼저 실행해야 합니다.  
(비밀번호나 컨테이너 이름 등은 수정해도 되나 아래 `askhy` 컨테이너 실행시 알맞게 설정해야 합니다)
```bash
docker run -d \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=askhy \
  --name mysql \
  mysql:5.7
```

---

다음 명령어를 입력해 build 합니다.
```bash
docker build -t askhy .
```

그 뒤에 이 명령어를 통해 해당 어플리케이션의 이미지를 다운로드하고 컨테이너를 실행합니다.

```bash
docker run -p 8080:80 \
  --link mysql:mysql_host \
  -e DATABASE_HOST=mysql_host \
  -e DATABASE_USER=root \
  -e DATABASE_PASS=root \
  -e DATABASE_NAME=askhy \
  --name askhy \
  prev/askhy
```
---

다음에 웹 브라우저를 열고 `localhost:8080` 에 접속하면 어플리케이션이 실행됩니다

## 프로젝트 Arcus
askhy_arcus 폴더에서 진행합니다. 

다음 명령어를 입력해 build 합니다.
```bash
docker build -t askhy_arcus .
```

그 뒤에 이 명령어를 통해 해당 어플리케이션의 이미지를 다운로드하고 컨테이너를 실행합니다.

```bash
docker run -p 8080:80 \
  --link mysql:mysql_host \
  -e DATABASE_HOST=mysql_host \
  -e DATABASE_USER=root \
  -e DATABASE_PASS=root \
  -e DATABASE_NAME=askhy _arcus\
  -e ARCUS_URL=172.17.0.2:2181 \
  -e ARCUS_SERVICE_CODE=ruo91-cloud \
  --name askhy_arcus \
  askhy_arcus
```
---

다음에 웹 브라우저를 열고 `localhost:8080` 에 접속하면 어플리케이션이 실행됩니다

## 프로젝트 nBase-ARC
askhy_nBase 폴더에서 진행합니다. 

다음 명령어를 입력해 build 합니다.
```bash
docker build -t askhy_nbase .
```

그 뒤에 이 명령어를 통해 해당 어플리케이션의 이미지를 다운로드하고 컨테이너를 실행합니다.

```bash
docker run -p 8080:80 \
  --link mysql:mysql_host \
  -e DATABASE_HOST=mysql_host \
  -e DATABASE_USER=root \
  -e DATABASE_PASS=root \
  -e DATABASE_NAME=askhy_nbase \
  -e REDIS_HOST=172.17.0.7 \
  -e REDIS_PORT=6000 \
  --name askhy_nbase \
  askhy_nbase
```
---

다음에 웹 브라우저를 열고 `localhost:8080` 에 접속하면 어플리케이션이 실행됩니다

---

## 프로젝트 nGrinder

mysql, nbase-arc, arcus-memcached 의 성능 측정을 위해 ngrinder 를 사용했습니다. mysql 만 사용했을 때와 arcus-memcached를 캐시로 사용했을 때 성능을 테스트 했습니다.
