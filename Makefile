include MakefileConstants.mk

#################
#
# Init Targets
#
#################

init-backend: check-py-virtualenv
	pip install -q -r backend/requirements-dev.txt

#################
#
# Prerequisite checks
#
#################
.PHONY: check-py-virtualenv                                                             ## Verify python dev environment
check-py-virtualenv: $(PYTHON_VERIFICATION_FILE)
$(PYTHON_VERIFICATION_FILE):
	@if [ -n "$(VIRTUAL_ENV)" ] ; then \
		printf "$(INFO_COLOR)OK:$(NO_COLOR) python virtual env found at $(VIRTUAL_ENV) - all good!\n" ; \
		date > $@ ; \
	else \
		printf "$(ERROR_COLOR)ERROR:$(NO_COLOR) python virtual env not found. Please install and configure a virtual env!\n" ; \
		exit 1 ; \
	fi


#################
#
# Deploy Targets
#
#################

.PHONY: deploy
deploy: build-layer sam-build check-environment-arg
	sam deploy \
		--s3-bucket ${service}-deployment \
		--stack-name ${service}-$(environment) \
		--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
		--profile $(awsProfile) \
		--parameter-overrides \
					Service=${service} \
					Environment=$(environment) \
					Bucket=$(bucket) \
					BucketRegion=$(region) \
					BcoDmoOfficeURI=$(bcodmoOfficeURI) \

.PHONY: sam-build
sam-build:
	sam build --use-container

# target only runs when requirements.txt is newer than package folder
PACKAGE_FOLDER := package
.PHONY: build-layer
build-layer: $(PACKAGE_FOLDER)
$(PACKAGE_FOLDER): backend/requirements.txt    ## install requirements into $(PACKAGE_FOLDER) when requirements.txt is newer than the folder
	rm -rf $(PACKAGE_FOLDER)
	pip install --target package/python -r backend/requirements.txt


#################
#
# Cleanup
#
#################

.PHONY: clean
clean: clean-backend-deploy clean-tox clean-pyc

.PHONY: clean-backend-deploy
clean-backend-deploy:
	rm -rf package

.PHONY: gone
gone: check-environment-arg
	aws cloudformation delete-stack --stack-name ${service}-$(environment)

#################
#
# Helper Targets
#
#################

.PHONY: check-environment-arg
check-environment-arg:
	@if [ -z "$${environment}" ] ; then make environment-not-set ; make cfn_help ; exit 1 ; fi

# Add an implicit guard for parameter input validation; use as target dependency guard-VARIABLE_NAME, e.g. guard-AWS_ACCESS_KEY_ID
.PHONY: %-not-set
%-not-set:
	@if [ "${${*}}" = "" ]; then \
		printf \
			"$(ERROR_COLOR)ERROR:$(NO_COLOR) Variable [$(ERROR_COLOR)$*$(NO_COLOR)] not set.\n"; \
		exit 1; \
	fi

.PHONY: cfn_help
cfn_help:                                ## print help for make (deploy|remove) targets
	@printf "\nmake (deploy|gone)\n"
	@printf "Usage:\n"
	@printf "    make awsprofile=<aws-profile> environment=<dpp2prov-environment> bucket=<dataset-pipelines-bucket> region=<region-for-bucket> bcodmoOfficeURI=<linked-data-uri> deploy\n"
	@printf "\n"
	@printf "Required:\n"
	@printf "    awsProfile:        The AWS credentials profile to deploy from.\n"
	@printf "    environment:       dpp2prov environment, unique \"environment\" e.g. \"dev\" or \"prod\".\n"
	@printf "    bucket:            AWS S3 bucket where dataset pipelines can be found.\n"
	@printf "    region:            The AWS region for the S3 bucket of dataset pipelines.\n"
	@printf "    bcodmoOfficeURI:	The Linked Data URI for the BCO-DMO Organization.\n"
	@printf "\n"

.PHONY: help
help:                                    ## Prints the names and descriptions of available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
