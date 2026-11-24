# Shadow starter
Create a separate shadow deployment with `SHADOW_MODE=true` and a separate service. Configure an ingress/proxy mirror to copy traffic to that service only after ingress is installed. Shadow instance must not write to production data. No mirror configuration is validated here.
