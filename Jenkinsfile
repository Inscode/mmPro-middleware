pipeline {
    agent any

    environment {
        DOCKER_HUB_REPO = 'inscodelk/mmpro'
        IMAGE_NAME = "${DOCKER_HUB_REPO}"
        REGISTRY_CREDENTIALS = 'dockerhub-creds'
        GIT_REPO = 'https://github.com/Inscode/mmPro-middleware'
        GIT_CREDENTIALS = 'git-creds'
        DEPLOYMENT_FILE = 'deployment.yaml'
        IMAGE_TAG = "v${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: "${GIT_REPO}", credentialsId: "${GIT_CREDENTIALS}"
            }
        }

        stage('Build & Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    mkdir -p .cache
                    export DISKCACHE_DIR=.cache
                    pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('', "${REGISTRY_CREDENTIALS}") {
                        dockerImage.push()
                    }
                }
            }
        }

        stage('Update Deployment YAML') {
            steps {
                script {
                    sh "sed -i 's|image: .*|image: ${IMAGE_NAME}:${IMAGE_TAG}|' ${DEPLOYMENT_FILE}"
                }
            }
        }

        stage('Push Updated YAML to Git') {
            steps {
                withCredentials([usernamePassword(credentialsId: "${GIT_CREDENTIALS}", usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                    sh '''
                        git config user.name "Jenkins"
                        git config user.email "jenkins@example.com"
                        git add ${DEPLOYMENT_FILE}
                        git commit -m "Update image to ${IMAGE_NAME}:${IMAGE_TAG}"
                        git push https://${GIT_USER}:${GIT_PASS}@github.com/your-username/mmpro-deployment.git HEAD:main
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "✅ CI/CD Pipeline completed successfully. Argo CD will auto-sync changes."
        }
        failure {
            echo "❌ Pipeline failed. Check Jenkins logs for details."
        }
    }
}

