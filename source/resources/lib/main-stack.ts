import {StackProps, CfnParameter, CfnOutput} from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import {Construct} from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import {AOSStack} from './aos/aos-stack';
// import { LLMStack } from './model/llm-stack';
import {ECSStack} from './ecs/ecs-stack';
import {CognitoStack} from './cognito/cognito-stack';
import {RDSStack} from './rds/rds-stack';
import {VPCStack} from './vpc/vpc-stack';

interface MainStackProps extends StackProps {
    deployRds?: boolean;
    bedrock_region: string;
    existing_vpc_id: string;
    cognito_sign_in_aliases_username?: boolean;
    embedding_platform : string;
    embedding_name : string;
    embedding_dimension : number;
    br_client_url: string;
    br_client_key: string;
    bedrock_ak_sk: string;
    sql_index: string;
    ner_index: string;
    cot_index: string;
    log_index: string;
    embedding_region: string;
}

export class MainStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: MainStackProps = {
        deployRds: false,
        bedrock_region: cdk.Aws.REGION,
        existing_vpc_id: "",
        cognito_sign_in_aliases_username: false,
        embedding_platform: "bedrock",
        embedding_name: "amazon.titan-embed-text-v1",
        embedding_dimension : 1536,
        br_client_url: "",
        br_client_key: "",
        sql_index: "uba",
        ner_index: "uba_ner",
        cot_index: "uba_agent",
        log_index: "genbi_query_logging",
        bedrock_ak_sk: "",
        embedding_region: cdk.Aws.REGION
    }) {
        super(scope, id, props);

        const _deployRds = props.deployRds || false;

        // ======== Step 0. Define the VPC =========
        const _VpcStack = new VPCStack(this, 'vpc-Stack', {
            env: props.env,
            existing_vpc_id: props.existing_vpc_id
        });


        // ======== Step 2. Define the AOSStack =========
        const aosSubnets = _VpcStack.vpc.selectSubnets({subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS});

        const _AosStack = new AOSStack(this, 'aos-Stack', {
            env: props.env,
            vpc: _VpcStack.vpc,
            subnets: aosSubnets.subnets,
        });

        // print AOS subnet Info
        console.log('AOS subnets Info:');
        aosSubnets.subnets.forEach((subnet, index) => {
            console.log(`Subnet ${index + 1}:`);
            console.log(`  ID: ${subnet.subnetId}`);
            console.log(`  Availability Zone: ${subnet.availabilityZone}`);
            console.log(`  CIDR: ${subnet.ipv4CidrBlock}`);
        });

        // print AOS subnet length
        console.log(`Total number of AOS subnets: ${aosSubnets.subnets.length}`);


        const aosEndpoint = _AosStack.endpoint;

        // ======== Step 4. Define Cognito =========
        const isChinaRegion = props.env?.region === "cn-north-1" || props.env?.region === "cn-northwest-1";

        let _CognitoStack: CognitoStack | undefined;
        if (!isChinaRegion) {
            _CognitoStack = new CognitoStack(this, 'cognito-Stack', {
                env: props.env,
                sign_in_aliases_username: props.cognito_sign_in_aliases_username
            });
        }


        // ======== Step 5. Define the ECS =========
        // pass the aosEndpoint and aosPassword to the ecs stack
        const ecsSubnets = _VpcStack.vpc.selectSubnets({subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS});

        // print AOS subnet Info
        console.log('ECS subnets Info:');
        ecsSubnets.subnets.forEach((subnet, index) => {
            console.log(`Subnet ${index + 1}:`);
            console.log(`  ID: ${subnet.subnetId}`);
            console.log(`  Availability Zone: ${subnet.availabilityZone}`);
            console.log(`  CIDR: ${subnet.ipv4CidrBlock}`);
        });

        // print AOS subnet length
        console.log(`Total number of ECS subnets: ${ecsSubnets.subnets.length}`);


        const _EcsStack = new ECSStack(this, 'ecs-Stack', {
                env: props.env,
                vpc: _VpcStack.vpc,
                subnets: ecsSubnets.subnets,
                authenticationType: _CognitoStack ? "Cognito" : "None",
                cognitoUserPoolId: _CognitoStack?.userPoolId ?? "",
                cognitoUserPoolClientId: _CognitoStack?.userPoolClientId ?? "",
                oidc_jwks_url: _CognitoStack?.userPoolProviderUrl ?? "",
                oidc_audience: "null",
                oidc_options: '{"verify_signature": true, "verify_aud": false}',
                OSMasterUserSecretName: _AosStack.OSMasterUserSecretName,
                OSHostSecretName: _AosStack.OSHostSecretName,
                bedrock_region: props.bedrock_region,
                embedding_platform: props.embedding_platform,
                embedding_name: props.embedding_name,
                embedding_dimension: props.embedding_dimension,
                br_client_url: props.br_client_url,
                br_client_key: props.br_client_key,
                bedrock_ak_sk: props.bedrock_ak_sk,
                sql_index: props.sql_index,
                ner_index: props.ner_index,
                cot_index: props.cot_index,
                log_index: props.log_index,
                embedding_region: props.embedding_region
            })
        ;

        _AosStack.addDependency(_VpcStack);
        _EcsStack.addDependency(_AosStack);
        if (_CognitoStack) {
            _EcsStack.addDependency(_CognitoStack);
        }
        _EcsStack.addDependency(_VpcStack);

        // ======== Step 3. Define the RDSStack =========
        if (_deployRds) {
            const rdsSubnets = _VpcStack.vpc.selectSubnets({subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS});

            const _RdsStack = new RDSStack(this, 'rds-Stack', {
                env: props.env,
                subnets: rdsSubnets,
                vpc: _VpcStack.vpc
            });

            _RdsStack.addDependency(_EcsStack);

            if (_RdsStack.rdsSecurityGroup && _EcsStack.ecsSecurityGroup) {
                _RdsStack.rdsSecurityGroup.addIngressRule(
                    _EcsStack.ecsSecurityGroup,
                    ec2.Port.tcp(3306),
                    'Allow inbound traffic from ECS on port 3306'
                );
            }
            new cdk.CfnOutput(this, 'RDSEndpoint', {
                value: _RdsStack.endpoint,
                description: 'The endpoint of the RDS instance',
            });
        }

        new cdk.CfnOutput(this, 'AOSDomainEndpoint', {
            value: aosEndpoint,
            description: 'The endpoint of the OpenSearch domain'
        });

        new cdk.CfnOutput(this, 'StreamlitEndpoint', {
            value: _EcsStack.streamlitEndpoint,
            description: 'The endpoint of the Streamlit service'
        });
        new cdk.CfnOutput(this, 'FrontendEndpoint', {
            value: _EcsStack.frontendEndpoint,
            description: 'The endpoint of the Frontend service'
        });
        new cdk.CfnOutput(this, 'APIEndpoint', {
            value: _EcsStack.apiEndpoint,
            description: 'The endpoint of the API service'
        });
    }
}
