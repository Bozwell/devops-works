### 외부 서비스용 nginx-ingress 설치

2-service-l7.yaml

aws certificate arn 주소를 입력한다.

```yaml
service.beta.kubernetes.io/aws-load-balancer-ssl-cert: ""
```



아래의 순서로 resource를 생성한다.

```bash
$ cd nginx-ingress
$ kubectl apply -f ./1-mandatory.yaml
$ kubectl apply -f ./2-service-l7.yaml
$ kubectl apply -f ./3-patch-configmap-l7.yaml
```



### 내부 서비스용 nginx-ingress 설치

생성되는 로드밸런서의 SecurityGroup은 기본적으로 "0.0.0.0/0"으로 설정되는데, 생성시점에서 아래와 같이 IP를 지정할 수 있다. 

```yaml
service.beta.kubernetes.io/load-balancer-source-ranges: "10.20.31.12/0"
```



아래의 순서로 resource를 생성한다.

```bash
$ cd nginx-ingress-internal
$ kubectl apply -f ./1-mandatory.yaml
$ kubectl apply -f ./2-service-l7.yaml
$ kubectl apply -f ./3-patch-configmap-l7.yaml
```

