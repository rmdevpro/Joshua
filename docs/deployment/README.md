# Deployment Documentation

## Overview
This directory contains deployment plans, testing suites, and post-mortem analyses for Joshua project deployments.

## Recent Deployments

### Relay V3.6 - Production Deployment (2025-10-09)
- **Status**: ✅ Successfully Deployed
- **Version**: 3.6.0
- **Key Change**: Fixed file locking to prevent lock file accumulation
- **Documents**:
  - [Deployment Plan](./relay_v3.6_deployment_plan.md)
  - [Testing Suite](./relay_v3.6_testing_suite.md)
  - [Post-Mortem Analysis](./relay_v3.6_post_mortem.md)

## Key Learnings from Deployments

### From Relay V3.6 Deployment:
1. **Multiple Reviewers are Critical**: DeepSeek caught a bug that GPT-4o missed
2. **Skip Known Limitations**: Don't test stdio services in containers
3. **Minimal Fix Strategy Works**: Fix critical issues first, defer nice-to-haves
4. **Trust the Process**: Review cycle prevented production issues

## Deployment Process

Our standard deployment process follows these phases:

1. **Pre-Deployment Preparation**
   - Extract code from development
   - Apply required fixes
   - Prepare test environment

2. **Fix Loop**
   - Apply fixes from review
   - Test basic functionality
   - Iterate until stable

3. **Test Loop**
   - Run unit tests
   - Run integration tests
   - Validate all connections

4. **Full Code Review**
   - Trio review (Gemini, GPT-4o, DeepSeek)
   - Senior synthesis
   - Junior validation

5. **Production Deployment**
   - Create backup
   - Deploy to production
   - Verify all systems
   - Update documentation

## Best Practices

1. **Always Create Backups**: Enable quick rollback if needed
2. **Test Everything**: MCP tools, backend connections, integrations
3. **Document Everything**: Keep detailed notes for post-mortems
4. **Review Disagreements Matter**: Don't dismiss minority opinions
5. **Follow the Process**: Even when it seems like overkill

## Metrics to Track

- Deployment duration
- Number of review iterations
- Issues caught in review
- Production impact
- Time to resolution

## Future Improvements

1. Automate token limit configuration for different models
2. Create pre-flight checklist for known limitations
3. Implement automated rollback triggers
4. Add performance regression detection