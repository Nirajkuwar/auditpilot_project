#!/bin/bash
set -e
ID=$(aws ec2 describe-instances --region $AWS_REGION \
  --filters Name=tag:Name,Values=auditpilot_app Name=instance-state-name,Values=running \
  --query 'Reservations[0].Instances[0].InstanceId' --output text)
CMD=$(aws ssm send-command --region $AWS_REGION --instance-ids $ID \
  --document-name AWS-RunShellScript \
  --parameters commands="/opt/auditpilot/deploy.sh $BUILD_NUMBER" \
  --query Command.CommandId --output text)
sleep 5
for i in $(seq 1 60); do
  S=$(aws ssm get-command-invocation --region $AWS_REGION --command-id $CMD \
    --instance-id $ID --query Status --output text || true)
  echo "status: $S"
  [ "$S" = "Success" ] && exit 0
  [ "$S" = "Failed" ] && break
  sleep 5
done
aws ssm get-command-invocation --region $AWS_REGION --command-id $CMD \
  --instance-id $ID --query StandardErrorContent --output text
exit 1
