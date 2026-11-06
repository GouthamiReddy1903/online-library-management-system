
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

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .'
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed. Check stage results above.'
        }
    }
}