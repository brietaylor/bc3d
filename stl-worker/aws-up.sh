podman build . -t jefftaylor42/bc3d_demproc
podman push jefftaylor42/bc3d_demproc
ecs-cli compose -f aws-compose.yml --ecs-params ecs-params.yml --project-name bc3d create

# I *would* just run "ecs-cli compose up" instead of "create", but I couldn't
# find any way to set capacityProvider to Spot.  So here we are, being
# redundant.  Shrug.
aws ecs run-task \
	--capacity-provider-strategy capacityProvider=FARGATE_SPOT \
	--cluster bc3d-demproc \
	--task-definition bc3d \
	--network-configuration "awsvpcConfiguration={subnets=[subnet-02728a5f],securityGroups=[sg-058b3aa052c227a5d],assignPublicIp=ENABLED}"
