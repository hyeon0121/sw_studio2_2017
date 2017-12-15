# sw2 프로젝트 
* 오픈소스 소프트웨어를 이용하여 DataBase System들의 성능 비교
* docker를 이용하여 MySQL, Arcus, nBase-ARC, nGrinder 사용

## Installation Guide
---

#### 1. docker 이미지 pull 

```bash
docker pull ruo91/arcus
```

#### 2. HostOS에서 Arcus Admin과 Memcached로 사용될 Container의 이미지를 생성
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

#### 3. 1 Zookeeper 설정

```bash
root@arcus:/opt/arcus/scripts# sed -i 's/127.0.0.1:2181/172.17.0.3:2181,172.17.0.4:2181,172.17.0.5:2181/g' arcus.sh
```

#### 3. 2 SSH Public Key 생성 및 배포

```bash
root@arcus:/opt/arcus/scripts# ssh-keygen -t dsa -P '' -f "/root/.ssh/id_dsa"
root@arcus:/opt/arcus/scripts# cat /root/.ssh/id_dsa.pub >> /root/.ssh/authorized_keys
root@arcus:/opt/arcus/scripts# chmod 644 /root/.ssh/authorized_keys
root@arcus:/opt/arcus/scripts# scp /root/.ssh/authorized_keys root@172.17.0.3:/root/.ssh
root@arcus:/opt/arcus/scripts# scp /root/.ssh/authorized_keys root@172.17.0.4:/root/.ssh
root@arcus:/opt/arcus/scripts# scp /root/.ssh/authorized_keys root@172.17.0.5:/root/.ssh
```

#### 3. 3 캐시 클라우드 설정

```bash
root@arcus:/opt/arcus/scripts# nano conf/ruo91.json
```

#### 4. Arcus 배포
memcached-1, memcached-2, memcached-3 서버에 arcus를 배포합니다 .

```bash
root@arcus:/opt/arcus/scripts# ./arcus.sh deploy conf/ruo91.json
```

#### 5. Zookeeper 앙상블 설정 및 실행

```bash
root@arcus:/opt/arcus/scripts# ./arcus.sh zookeeper init
root@arcus:/opt/arcus/scripts# ./arcus.sh zookeeper start
```

#### 6. Memcached 등록 및 실행

```bash
root@arcus:/opt/arcus/scripts# ./arcus.sh memcached register conf/ruo91.json
root@arcus:/opt/arcus/scripts# ./arcus.sh memcached start ruo91-cloud
```

#### 7. docker 에서 arcus-admin, Arcus-memcached-1 ,Arcus-memcached-2, Arcus-memcached-3 순서대로 켜줍니다.

#### 8. docker network inspect bridge 를 입력해 IP를 맞춰주고 Database 이름과 build 한 이름을 맞춰주면 됩니다.

---