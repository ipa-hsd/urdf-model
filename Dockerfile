FROM moveit/moveit2:humble-release

RUN apt-get update \
    && apt-get install -y git \
        python3-pip \
        graphviz \
        jq \
        ros-humble-tf-transformations \
        maven

RUN pip3 install bigtree \
    bigtree[image] \
    bigtree[pandas] \
    flask \
    flask_socketio \
    flask_sqlalchemy \
    jsonschema \
    pyecore \
    requests \
    ruamel.yaml \
    transforms3d

RUN mkdir /ls \
    && cd /ls \
    && git clone --single-branch --branch main https://github.com/ipa320/kinematics-model.git

WORKDIR /ls/kinematics-model/de.fraunhofer.ipa.kinematics.xtext.parent
RUN mvn clean install -U -DskipTests

RUN mkdir /app \
    && cd /app \
    && git clone --single-branch --branch main https://github.com/ipa-hsd/kinematic_components_web_app

RUN mkdir -p /app/kinematic_components_web_app/static/moveit2_ws/src
WORKDIR /app/kinematic_components_web_app/static/moveit2_ws/src

RUN git clone --single-branch --branch main https://github.com/ipa-hsd/urdf-model

COPY ./component_list.yaml ./urdf-model/

# clone the repositories specified in component_list.yaml
RUN chmod +x ./urdf-model/kinematics-model-parser/scripts/clone_packages.sh \
    && /bin/bash -c './urdf-model/kinematics-model-parser/scripts/clone_packages.sh \
        "./urdf-model/component_list.yaml" \
        "/app/kinematic_components_web_app/static/moveit2_ws/src"'

WORKDIR /app/kinematic_components_web_app/static/moveit2_ws

RUN . /opt/ros/humble/setup.sh \
    && colcon build \
    && . ./install/setup.sh

WORKDIR /app/kinematic_components_web_app

#start the kinematic components web app
EXPOSE 5500
# CMD [ "flask", "--app", "/app/kinematic_components_web_app/app", "run", "--host", "0.0.0.0", "--port", "5500"]