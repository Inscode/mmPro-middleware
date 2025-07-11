pipeline {
    agent any

    environment {
        // Docker config
        DOCKER_HUB_REPO = 'inscodelk/mmpro'
        IMAGE_TAG = "v${env.BUILD_NUMBER}"
        REGISTRY_CREDENTIALS = 'dockerhub-creds'

        // Git config
        GIT_BRANCH = 'main'
        GIT_CREDENTIALS = 'git-ssh-key'

        // K8s manifest files
        DEPLOYMENT_FILE = 'k8s/deployment.yaml'
        ARGOCD_APP_FILE = 'k8s/argocd-app.yaml'

        // ArgoCD config
        ARGOCD_SERVER = 'argocd.aasait.lk'
        ARGOCD_APP_NAME = 'mmpro-application'
    }

    stages {
           stage('Build & Test') {
                steps {
                    dir('.') {
                        sh '''#!/bin/bash -xe
                            # Create and activate virtual environment
                            python3 -m venv venv
                            source venv/bin/activate
                            
                            # Upgrade pip and install dependencies
                            pip install --upgrade pip
                            pip install -r requirements.txt
                            
                            # Install test-specific requirements
                            pip install pytest pytest-cov
                            
                            # Diagnostic output
                            echo "PYTHONPATH: ${PYTHONPATH:-Not Set}"
                            echo "Current directory: $(pwd)"
                            echo "Test directory contents:"
                            ls -l tests/
                            
                            # Run pytest with explicit path
                            PYTHONPATH=$(pwd) pytest \
                                tests/ \
                                -v \
                                --junitxml=test-results.xml \
                                --cov=app \
                                --cov-report=xml:coverage.xml || true
                        '''
                    }
                }
        }

        stage('Build Docker Image') {
            steps {
                dir('.') {
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
                dir('.') {
                    sh """
                        sed -i 's|image: .*|image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}|' ${DEPLOYMENT_FILE}
                        sed -i 's|targetRevision: .*|targetRevision: ${GIT_BRANCH}|' ${ARGOCD_APP_FILE}
                    """
                }
            }
        }

        stage('Commit & Push Changes') {
            steps {
                dir('.') {
                    sshagent(credentials: ["${GIT_CREDENTIALS}"]) {
                        sh '''
                            git config user.name "Inscode"
                            git config user.email "insaf.ahmedh@gmail.com"
                            git remote set-url origin git@github.com:Inscode/mmPro-middleware.git
                            
                            # Discard all local changes
                            git reset --hard
                            
                            # Force sync with remote
                            git fetch origin main
                            git checkout -B main origin/main
                            
                            git add ${DEPLOYMENT_FILE} ${ARGOCD_APP_FILE}
                            git commit -m "[CI] Update to ${DOCKER_HUB_REPO}:${IMAGE_TAG}" || echo "No changes to commit"
                            git push origin main
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
