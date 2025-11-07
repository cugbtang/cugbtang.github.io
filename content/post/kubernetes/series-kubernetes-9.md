---
title: "kubernetes admission,how to play?"
date: 2022-04-15T16:01:23+08:00
lastmod: 2022-04-15T16:01:23+08:00
draft: false
tags: ["image", "FAQ"]
categories: ["cloudnative"]
author: "yesplease"
---

# Admission

## 一、static admission controllers

[官方内置](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)，启用就行


## 二、dynamic admission controllers

[官方介绍](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)

简单流程：

- 创建一个web服务（tls）
- 自签发证书
- 创建Dockerfile和deployment service 文件
- 创建MutatingWebhookConfiguration资源

```sh
#!/bin/bash
name=mywebhook
namespace=mynamespace
go mod init ${name}
cat <<EOF > ./main.go
package main

import (
    "context"
    "encoding/json"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"

    admissionv1 "k8s.io/api/admission/v1"
    corev1 "k8s.io/api/core/v1"

    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

type jsonPatch struct {
    OP    string      \`json:"op"\`
    Path  string      \`json:"path"\`
    Value interface{} \`json:"value"\`
}
s
func podsMutate(w http.ResponseWriter, r *http.Request) {
    admissionReviewReq := &admissionv1.AdmissionReview{}
    if err := json.NewDecoder(r.Body).Decode(admissionReviewReq); err != nil {
        return
    }

    pod := &corev1.Pod{}
    if err := json.Unmarshal(admissionReviewReq.Request.Object.Raw, pod); err != nil {
        return
    }

    labels := pod.Labels
    if pod.Labels == nil {
        labels = make(map[string]string)
    }
    labels["a"] = "1"
    var patchs []jsonPatch
    patchs = append(patchs, jsonPatch{
        OP:    "add",
        Path:  "/metadata/labels",
        Value: labels,
    })

    jsonPatchata, err := json.Marshal(patchs)
    if err != nil {
        return
    }

    patchType := admissionv1.PatchTypeJSONPatch

    resp := &admissionv1.AdmissionResponse{
        UID:       admissionReviewReq.Request.UID,
        Allowed:   true,
        Patch:     jsonPatchata,
        PatchType: &patchType,
    }

    admissionReviewResp := &admissionv1.AdmissionReview{
        TypeMeta: metav1.TypeMeta{
            Kind:       "AdmissionReview",
            APIVersion: "admission.k8s.io/v1",
        },
        Response: resp,
    }
    if err := json.NewEncoder(w).Encode(admissionReviewResp); err != nil {
        return
    }

}

func main() {

    mux := http.NewServeMux()
    server := &http.Server{
        Handler: mux,
    }

    mux.HandleFunc("/pods/mutate", podsMutate)

    ch := make(chan os.Signal, 1)
    signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
    go func() {
        <-ch
        server.Shutdown(context.TODO())
    }()

    if err := server.ListenAndServeTLS("/etc/${name}/tls.crt", "/etc/${name}/tls.key"); err != nil &&
        err != http.ErrServerClosed {
        log.Fatalf("Failed to ListenAndServeTLS, err:%#v", err)
    }
}
EOF

go mod tidy



cat <<EOF > ./Dockerfile
FROM golang:alpine as builder
ENV GO111MODULE=on \
    GOPROXY=https://goproxy.cn,direct
ARG CONF=dev
WORKDIR /go/app
COPY go.mod .
COPY go.sum .
RUN go mod download
COPY main.go main.go
RUN CGO_ENABLED=0 GOARCH=amd64 GOOS=linux go build -o app .

FROM alpine:latest as prod
ARG CONF=dev
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && apk --no-cache add ca-certificates && apk add tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone
WORKDIR /app/
COPY --from=0 /go/app/app .
CMD ["./app"]
EOF

docker build -t mywebhook:0.1 .



kubectl create ns ${namespace}

openssl genrsa -out ca.key 2048

openssl req -new -x509 -days 365 -key ca.key \
  -subj "/C=AU/CN=${name}"\
  -out ca.crt

openssl req -newkey rsa:2048 -nodes -keyout server.key \
  -subj "/C=AU/CN=${name}" \
  -out server.csr

openssl x509 -req \
  -extfile <(printf "subjectAltName=DNS:${name}.${namespace}.svc") \
  -days 365 \
  -in server.csr \
  -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt


kubectl create secret tls -n ${namespace} ${name} \
  --cert=server.crt \
  --key=server.key \
  --dry-run=client -o yaml \
  > ./secret.yaml


caBundle=`cat ca.crt | base64 | fold |awk BEGIN{RS=EOF}'{gsub(/\n/,"");print}'`
cat <<EOF > ./webhook.yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
 name: ${name}
 namespace: ${namespace}
webhooks:
- name: ${name}.${namespace}.com
  failurePolicy: "Fail"
  matchPolicy: "Equivalent"
  rules:
    - apiGroups: [""]
      apiVersions: ["v1"]
      operations: ["CREATE","UPDATE"]
      resources: ["pods"]
      scope: "*"
  clientConfig:
    service:
      namespace: ${namespace}
      name: ${name}
      path: /pods/mutate
      port: 443
    caBundle: ${caBundle}
  admissionReviewVersions: ["v1", "v1beta1"]
  sideEffects: None
  timeoutSeconds: 10
  reinvocationPolicy: "Never"
EOF



cat <<EOF > ./deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${name}
  namespace: ${namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${name}
  template:
    metadata:
      labels:
        app: ${name}
    spec:
      containers:
        - image: ${name}:0.1
          imagePullPolicy: Never
          name: app
          volumeMounts:
            - name: tls
              mountPath: "/etc/${name}"
              readOnly: true
      volumes:
        - name: tls
          secret:
            secretName: ${name}
EOF


cat <<EOF > ./service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ${name}
  namespace: ${namespace}
spec:
  type: ClusterIP
  ports:
    - port: 443
      protocol: TCP
      targetPort: 443
  selector:
    app: ${name}
EOF


cat <<EOF > ./demo.yaml
apiVersion: v1
kind: Pod
metadata:
  name: demo
  namespace: ${namespace}
spec:
  containers:
  - command:
       - sh
       - -c
       - 'sleep 10'
    image: busybox
    name: busybox
EOF

```

### 2. 部署webhook

```sh
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f webhook.yaml

rm ca.crt ca.key ca.srl server.crt server.csr server.key
```

### 3. 部署demo

```sh
#创建webhook相关以及demo pod yaml
bash webhook.sh 
kubectl apply -f demo.yaml
```

