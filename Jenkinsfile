pipeline {
    agent any

    environment {
        // Docker Configuration
        DOCKER_HUB_REPO = 'inscodelk/mmpro'
        IMAGE_NAME = "${DOCKER_HUB_REPO}"
        REGISTRY_CREDENTIALS = 'dockerhub-creds'
        
        // Git Configuration
        GIT_REPO = 'https://github.com/Inscode/mmPro-middleware.git'
        GIT_CREDENTIALS = 'git-creds'
        GIT_BRANCH = 'main'
        
        // Kubernetes Manifests
        DEPLOYMENT_FILE = 'deployment.yaml'
        SERVICE_FILE = 'service.yaml'
        ARGOCD_APP_FILE = 'argocd-app.yaml'
        
        // ArgoCD Configuration
        ARGOCD_SERVER = 'https://argocd.aasait.lk' // Update with your ArgoCD URL
        ARGOCD_APP_NAME = 'mmpro-application'
        
        // Versioning
        IMAGE_TAG = "v${env.BUILD_NUMBER}"
    }

    stages {
        // Stage 1: Checkout Code
        stage('Checkout Code') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "${GIT_BRANCH}"]],
                    extensions: [],
                    userRemoteConfigs: [[
                        credentialsId: "${GIT_CREDENTIALS}",
                        url: "${GIT_REPO}"
                    ]]
                ])
            }
        }

        // Stage 2: Build & Test
        stage('Build & Test') {
            steps {
                sh '''
                    set -e
                    /usr/bin/python3.11 -m venv venv --clear
                    ./venv/bin/pip install --upgrade pip
                    ./venv/bin/pip install -r requirements.txt
                    mkdir -p .cache
                    export DISKCACHE_DIR=.cache
                    echo "🐍 Python version:" && ./venv/bin/python --version
                    ./venv/bin/python -m pytest
                '''
            }
        }

        // Stage 3: Build Docker Image
        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                }
            }
        }

        // Stage 4: Push Docker Image
        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('', "${REGISTRY_CREDENTIALS}") {
                        dockerImage.push()
                    }
                }
            }
        }

        // Stage 5: Update Kubernetes Manifests
        stage('Update Kubernetes Manifests') {
            steps {
                script {
                    // Update image tag in deployment.yaml
                    sh "sed -i 's|image: .*|image: ${IMAGE_NAME}:${IMAGE_TAG}|' ${DEPLOYMENT_FILE}"
                    
                    // Ensure argocd-app.yaml points to the correct branch
                    sh "sed -i 's|targetRevision: .*|targetRevision: ${GIT_BRANCH}|' ${ARGOCD_APP_FILE}"
                }
            }
        }

        // Stage 6: Push Changes to Git
        stage('Push Changes to Git') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${GIT_CREDENTIALS}",
                    usernameVariable: 'GIT_USER',
                    passwordVariable: 'GIT_PASS'
                )]) {
                    sh '''
                        git config user.name "Jenkins CI"
                        git config user.email "jenkins@example.com"
                        git add ${DEPLOYMENT_FILE} ${ARGOCD_APP_FILE}
                        git commit -m "[CI] Update to ${IMAGE_NAME}:${IMAGE_TAG}"
                        git push origin ${GIT_BRANCH}
                    '''
                }
            }
        }

        // Stage 7: Trigger ArgoCD Sync (Optional)
        stage('Trigger ArgoCD Sync') {
            steps {
                script {
                    withCredentials([string(credentialsId: 'argocd-api-token', variable: 'ARGOCD_TOKEN')]) {
                        sh """
                            curl -sS -X POST \
                            "https://${ARGOCD_SERVER}/api/v1/applications/${ARGOCD_APP_NAME}/sync" \
                            -H "Authorization: Bearer ${ARGOCD_TOKEN}" \
                            -H "Content-Type: application/json" \
                            --data '{}'
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            slackSend(
                color: 'good',
                message: "✅ Pipeline SUCCESS - ${IMAGE_NAME}:${IMAGE_TAG} deployed via ArgoCD"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "❌ Pipeline FAILED - Check ${env.BUILD_URL}"
            )
        }
    }
}
