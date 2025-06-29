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
        DEPLOYMENT_FILE = 'deployment.yaml'
        ARGOCD_APP_FILE = 'argocd-app.yaml'

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
                        
                        # Diagnostic output (helps debugging)
                        echo "Current directory structure:"
                        ls -l
                        echo "Test directory contents:"
                        ls -l tests/
                        
                        # Run pytest with explicit path and increased verbosity
                        PYTHONPATH=$PWD pytest \
                            tests/ \
                            -v \
                            --junitxml=test-results.xml \
                            --cov=./ \
                            --cov-report=xml:coverage.xml
                        
                        # Generate HTML coverage report (optional)
                        pip install pytest-cov
                        pytest --cov=./ --cov-report=html:htmlcov tests/
                    '''
                }
            }
            post {
                always {
                    junit 'test-results.xml'  # Archive test results
                    cobertura coberturaReportFile: 'coverage.xml'  # Archive coverage
                    archiveArtifacts artifacts: 'htmlcov/**'  # Archive HTML coverage (optional)
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
