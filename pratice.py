pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'ghcr.io/asifali515/calculator-app'
        DOCKER_REGISTRY = 'ghcr.io'
        GITHUB_CREDENTIALS_ID = 'personal_secret'
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'
        IMAGE_TAG = "latest"
        DEPLOY_TO_DOCKERHUB = true
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout code from the dev branch
                git branch: 'dev', credentialsId: "${personal_secret}", url: 'https://github.com/asifali515/calculator-app.git'
            }
        }

        stage('Build & Test') {
            steps {
                // Run tests
                script {
                    sh 'python3 -m unittest discover -s tests'
                }
            }
        }

        stage('Merge Dev to Main') {
            steps {
                script {
                    // Merge the dev branch into main
                    sh '''
                    git checkout main
                    git pull origin main
                    git merge dev
                    git push origin main
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build Docker image
                    if (env.BRANCH_NAME == 'main') {
                        IMAGE_TAG = "latest"
                    } else {
                        IMAGE_TAG = "dev-${BUILD_NUMBER}"
                    }

                    sh """
                        docker build -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${IMAGE_TAG} .
                    """
                }
            }
        }

        stage('Push Docker Image to DockerHub') {
            when {
                expression { DEPLOY_TO_DOCKERHUB == true }
            }
            steps {
                script {
                    // Login to DockerHub
                    withCredentials([usernamePassword(credentialsId: "${dockerhub_credentials}", passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
                        sh """
                            echo $DOCKER_PASSWORD | docker login --username $DOCKER_USERNAME --password-stdin
                        """
                    }

                    // Push Docker image to DockerHub
                    sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${IMAGE_TAG}"
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully."
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}
