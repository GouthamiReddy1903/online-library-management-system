
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'online-library-management'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                sh 'python3 -m venv .venv'
                sh '. .venv/bin/activate && pip install -r requirements.txt'
            }
        }

        stage('Unit Tests') {
            steps {
                sh '. .venv/bin/activate && python -m pytest -v'
            }
        }

        stage('Selenium Browser Tests') {
            steps {
                sh '''
                    set -eu

                    . .venv/bin/activate

                    RUN_SELENIUM=1 \
                    SELENIUM_REMOTE_URL=http://host.docker.internal:4444 \
                    APP_URL=http://host.docker.internal:5000 \
                    python -m pytest -v tests/test_selenium.py
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .'
            }
        }

        stage('Transfer Image to Kubernetes') {
            steps {
                sh '''
                    set -eu

                    IMAGE_TAG="${IMAGE_NAME}:${BUILD_NUMBER}"
                    IMAGE_TAR="/tmp/${IMAGE_NAME}-${BUILD_NUMBER}.tar"

                    docker save -o "$IMAGE_TAR" "$IMAGE_TAG"

                    docker cp "$IMAGE_TAR" desktop-control-plane:/root/library-image-${BUILD_NUMBER}.tar

                    docker exec desktop-control-plane ctr -n k8s.io images import /root/library-image-${BUILD_NUMBER}.tar

                    docker exec desktop-control-plane rm -f /root/library-image-${BUILD_NUMBER}.tar

                    rm -f "$IMAGE_TAR"
                '''
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                    set -eu

                    kubectl set image deployment/online-library library=${IMAGE_NAME}:${BUILD_NUMBER}

                    kubectl rollout status deployment/online-library --timeout=180s

                    kubectl get pods -l app=online-library
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed. Check stage results above.'
        }
    }
}
