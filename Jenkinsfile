pipeline {
    agent any

    environment {
        // Docker config
        DOCKER_HUB_REPO = 'inscodelk/mmpro'
        IMAGE_TAG = "v${env.BUILD_NUMBER}"
        REGISTRY_CREDENTIALS = 'dockerhub-creds'

        // Git config
        GIT_REPO = 'git@github.com:Inscode/mmPro-middleware.git'
        GIT_BRANCH = 'main'
        GIT_CREDENTIALS = 'git-ssh-key'

        // K8s manifest files
        DEPLOYMENT_FILE = 'deployment.yaml'
        ARGOCD_APP_FILE = 'argocd-app.yaml'

        // ArgoCD config
        ARGOCD_SERVER = 'argocd.aasait.lk'
        ARGOCD_APP_NAME = 'mmpro-application'
    }

    stages {
        stage('Checkout Code') {
            steps {
                sshagent(credentials: ["${GIT_CREDENTIALS}"]) {
                    sh "git clone -b ${GIT_BRANCH} ${GIT_REPO} app"
                }
                dir('app') {
                    script {
                        env.WORKSPACE = pwd()
                    }
                }
            }
        }

        stage('Build & Test') {
            steps {
                dir('app') {
                    sh '''
                        python3 -m venv venv
                        ./venv/bin/pip install --upgrade pip
                        ./venv/bin/pip install -r requirements.txt
                        ./venv/bin/python -m pytest
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                dir('app') {
                    script {
                        dockerImage = docker.build("${DOCKER_HUB_REPO}:${IMAGE_TAG}")
                    }
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

        stage('Update Manifests') {
            steps {
                dir('app') {
                    sh """
                        sed -i 's|image: .*|image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}|' ${DEPLOYMENT_FILE}
                        sed -i 's|targetRevision: .*|targetRevision: ${GIT_BRANCH}|' ${ARGOCD_APP_FILE}
                    """
                }
            }
        }

        stage('Commit & Push Changes') {
            steps {
                dir('app') {
                    sshagent(credentials: ["${GIT_CREDENTIALS}"]) {
                        sh '''
                            git config user.name "achintha aasait"
                            git config user.email "achintha@gmail.com"
                            git add ${DEPLOYMENT_FILE} ${ARGOCD_APP_FILE}
                            git commit -m "[CI] Update to ${DOCKER_HUB_REPO}:${IMAGE_TAG}" || echo "No changes to commit"
                            git push origin ${GIT_BRANCH}
                        '''
                    }
                }
            }
        }

        stage('Trigger ArgoCD Sync') {
            steps {
                withCredentials([string(credentialsId: 'argocd-api-token', variable: 'ARGOCD_TOKEN')]) {
                    sh '''
                        curl -sS -X POST \
                        -H "Authorization: Bearer ${ARGOCD_TOKEN}" \
                        -H "Content-Type: application/json" \
                        --data '{}' \
                        https://${ARGOCD_SERVER}/api/v1/applications/${ARGOCD_APP_NAME}/sync
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline SUCCESS - ${DOCKER_HUB_REPO}:${IMAGE_TAG} deployed via ArgoCD"
        }
        failure {
            echo "❌ Pipeline FAILED - Check build logs"
        }
    }
}
