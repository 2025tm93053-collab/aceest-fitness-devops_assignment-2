# Rolling update / rollback
Use a Deployment with `strategy: {type: RollingUpdate, rollingUpdate: {maxSurge: 1, maxUnavailable: 0}}`. Update its image, inspect `kubectl rollout status deployment/aceest-fitness`, and revert with `kubectl rollout undo deployment/aceest-fitness`. Validate in Minikube before claiming completion.
