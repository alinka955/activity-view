FROM python:3
FROM rockylinux:8

WORKDIR /activityview-app

RUN yum -y update
RUN yum install -y git
RUN dnf install -y python3.8
RUN git clone https://github.com/alinka955/activity-view.git /activityview-app
RUN git pull origin master

CMD ["echo", "Running activity-view"]
