const { awscdk } = require('projen');

const project = new awscdk.AwsCdkPythonApp({
  authorName: 'AWS Developer',
  authorEmail: 'developer@example.com',
  cdkVersion: '2.100.0',
  moduleName: 'eks_helm_deployment',
  name: 'eks-helm-deployment',
  
  deps: [
    'aws-cdk.lambda-layer-kubectl-v28@2.0.0',
    'boto3@1.34.0',
    'pytest@8.2.0',
    'pytest-cov@4.1.0',
  ],
  
  devDeps: [],
  
  github: false,
});

project.synth();
