# Ingress Configuration

This directory contains the Kubernetes ingress configuration for GoalTrajectory.AI, providing external traffic routing, SSL/TLS termination, and security features.

## Components

### 1. Ingress Resources (`ingress.yaml`)

- **Production Ingress**: Routes traffic for `goaltrajectory.ai` and `api.goaltrajectory.ai`
- **Development Ingress**: Routes traffic for `dev.goaltrajectory.ai` and `api-dev.goaltrajectory.ai`
- **Path-based Routing**: Alternative routing using `/api` path prefix
- **SSL/TLS Termination**: Automatic certificate management with Let's Encrypt

### 2. Certificate Management (`cert-issuer.yaml`)

- **Production Issuer**: Let's Encrypt production certificates
- **Staging Issuer**: Let's Encrypt staging certificates for testing
- **Automatic Renewal**: Certificates are automatically renewed before expiration

### 3. Security Configuration (`middleware.yaml`)

- **Rate Limiting**: Configurable request limits per IP and time window
- **Security Headers**: HSTS, CSP, X-Frame-Options, and other security headers
- **CORS Configuration**: Cross-origin resource sharing for API endpoints
- **SSL/TLS Settings**: Modern cipher suites and protocols

### 4. Network Policies (`ingress-network-policy.yaml`)

- **Ingress Traffic Control**: Restricts traffic to ingress controller
- **Service Communication**: Allows communication between ingress and services
- **DNS Resolution**: Permits DNS queries for service discovery

## Features

### SSL/TLS Security
- Automatic certificate provisioning with Let's Encrypt
- Modern TLS protocols (TLSv1.2, TLSv1.3)
- Strong cipher suites and security headers
- HSTS enforcement for enhanced security

### Rate Limiting
- **Production**: 60 requests/minute, 10 concurrent connections
- **Development**: 300 requests/minute, 50 concurrent connections
- **API Endpoints**: Higher limits for API traffic
- **Static Content**: Optimized limits for static assets

### Security Headers
- **X-Frame-Options**: Prevents clickjacking attacks
- **Content-Security-Policy**: Mitigates XSS and injection attacks
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **Referrer-Policy**: Controls referrer information leakage
- **Permissions-Policy**: Restricts browser feature access

### CORS Configuration
- **Development**: Permissive CORS for local development
- **Production**: Restricted CORS for security
- **Preflight Handling**: Proper OPTIONS request handling
- **Credential Support**: Secure cookie and authentication handling

## Deployment

### Prerequisites

1. **Kubernetes Cluster**: Running Kubernetes cluster (1.19+)
2. **NGINX Ingress Controller**: Will be installed by the deployment script
3. **cert-manager**: Will be installed for certificate management
4. **DNS Configuration**: Domain names pointing to cluster load balancer

### Quick Deployment

```bash
# Full deployment (recommended)
./deploy-ingress.sh

# Install components separately
./deploy-ingress.sh --install-controller-only
./deploy-ingress.sh --install-cert-manager-only
./deploy-ingress.sh --apply-configs-only

# Verify installation
./deploy-ingress.sh --verify-only
```

### Manual Deployment

```bash
# 1. Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# 2. Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml

# 3. Create namespaces
kubectl create namespace goaltrajectory
kubectl create namespace goaltrajectory-dev

# 4. Apply configurations
kubectl apply -f cert-issuer.yaml
kubectl apply -f middleware.yaml
kubectl apply -f ingress-network-policy.yaml
kubectl apply -f ingress.yaml
```

## Configuration

### Domain Names

Update the following files with your actual domain names:

1. **ingress.yaml**: Replace `goaltrajectory.ai` with your domain
2. **cert-issuer.yaml**: Replace email address with your admin email

### Environment-Specific Settings

#### Production
- Strict rate limiting and security headers
- Let's Encrypt production certificates
- Restricted CORS policies
- Enhanced network policies

#### Development
- Relaxed rate limiting for testing
- Let's Encrypt staging certificates
- Permissive CORS for development
- Basic security headers

### Rate Limiting Customization

Modify `middleware.yaml` to adjust rate limits:

```yaml
# Global rate limiting
rate-limit-rpm: "60"        # Requests per minute
rate-limit-rps: "10"        # Requests per second
rate-limit-connections: "10" # Concurrent connections

# API-specific limits
api-rate-limit-rpm: "120"
api-rate-limit-rps: "20"
```

### Security Headers Customization

Update security headers in `middleware.yaml`:

```yaml
# Content Security Policy
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline';" always;

# Additional security headers
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
```

## Monitoring and Troubleshooting

### Check Ingress Status

```bash
# View ingress resources
kubectl get ingress -n goaltrajectory
kubectl describe ingress goaltrajectory-ingress -n goaltrajectory

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# View certificate status
kubectl get certificates -n goaltrajectory
kubectl describe certificate goaltrajectory-tls -n goaltrajectory
```

### Common Issues

1. **Certificate Not Issued**
   - Check cert-manager logs: `kubectl logs -n cert-manager -l app=cert-manager`
   - Verify DNS configuration points to load balancer
   - Ensure HTTP-01 challenge can reach cluster

2. **Rate Limiting Too Strict**
   - Adjust rate limits in middleware configuration
   - Check ingress controller logs for rate limit hits

3. **CORS Issues**
   - Verify CORS configuration in middleware
   - Check browser developer tools for CORS errors
   - Ensure preflight requests are handled correctly

4. **SSL/TLS Issues**
   - Verify certificate issuer configuration
   - Check certificate status and renewal
   - Ensure TLS configuration is compatible with clients

## Security Considerations

### Network Security
- Network policies restrict traffic between services
- Ingress controller isolated in separate namespace
- Service-to-service communication controlled

### Certificate Security
- Automatic certificate rotation with Let's Encrypt
- Strong cipher suites and modern TLS protocols
- HSTS enforcement for enhanced security

### Application Security
- Rate limiting prevents abuse and DoS attacks
- Security headers protect against common web vulnerabilities
- CORS policies prevent unauthorized cross-origin requests

### Monitoring and Alerting
- Monitor certificate expiration dates
- Alert on rate limit violations
- Track security header compliance
- Monitor ingress controller health and performance

## Maintenance

### Regular Tasks
1. **Certificate Monitoring**: Ensure certificates renew automatically
2. **Security Updates**: Keep ingress controller and cert-manager updated
3. **Rate Limit Review**: Adjust limits based on traffic patterns
4. **Security Header Updates**: Update CSP and other headers as needed

### Backup and Recovery
- Export ingress configurations: `kubectl get ingress -o yaml`
- Backup certificate secrets: `kubectl get secrets -o yaml`
- Document DNS and load balancer configurations