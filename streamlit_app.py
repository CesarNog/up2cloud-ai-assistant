"""
UP2CLOUD Model - Streamlit Cloud Demo Interface
Deployed to Streamlit Cloud for free public access
"""

import streamlit as st
from model import predict
from enhanced_features import CostEstimator, SecurityScanner
import json

# Page config
st.set_page_config(
    page_title="UP2CLOUD AI Cloud Engineering Assistant",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { padding-top: 2rem; }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 18px;
        padding: 10px 20px;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown("""
# ☁️ UP2CLOUD AI Cloud Engineering Assistant

**Premium Cloud Engineering AI** - Get instant expert answers on AWS, GCP, Azure, Kubernetes, Terraform, DevOps, and FinOps

---
""")

# Sidebar
with st.sidebar:
    st.markdown("## 📋 Navigation")
    st.markdown("""
    This app provides cloud engineering guidance powered by AI.
    
    ### Features
    - 💬 Cloud Q&A
    - 💰 Cost Estimation
    - 🏗️ Code Generation
    - 📊 Architecture Diagrams
    - 🔒 Security Audit
    
    ### About UP2CLOUD
    A consulting company specializing in:
    - Platform Engineering
    - DevOps & Infrastructure
    - FinOps & Cost Optimization
    - Cloud Architecture
    
    **Website**: https://up2cloud.com
    """)

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Cloud Q&A", "💰 Cost Estimation", "🏗️ Code Generation", "📊 Architecture", "🔒 Security"])

# Tab 1: Cloud Q&A
with tab1:
    st.header("Cloud Engineering Q&A")
    st.markdown("""
    Ask any cloud engineering question. The AI will provide expert guidance based on your context.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        prompt = st.text_area(
            "Your Question",
            placeholder="e.g., How should we migrate to Kubernetes?",
            height=100
        )
        company_type = st.text_input(
            "Company Type (optional)",
            placeholder="e.g., SaaS Startup, Enterprise"
        )
    
    with col2:
        infrastructure = st.text_area(
            "Current Infrastructure (optional)",
            placeholder="e.g., EC2 + RDS on AWS",
            height=50
        )
        challenges = st.text_area(
            "Main Challenges (optional)",
            placeholder="e.g., Need to scale for 10x growth",
            height=50
        )
    
    if st.button("Get Answer", key="qa_btn", type="primary", use_container_width=True):
        if prompt:
            with st.spinner("Getting expert answer..."):
                context = {}
                if company_type:
                    context["company_type"] = company_type
                if infrastructure:
                    context["current_infrastructure"] = infrastructure
                if challenges:
                    context["challenges"] = challenges
                
                result = predict(prompt, context=context if context else None)
                
                st.markdown("### 💡 Answer")
                st.markdown(result.get('response', 'No response generated'))
                
                # Show metadata
                with st.expander("📊 Technical Details"):
                    st.json({
                        "tokens_used": result.get('usage', {}).get('total_tokens', 'N/A'),
                        "model": "UP2CLOUD v2.0",
                        "features_used": list(result.keys())
                    })
        else:
            st.warning("Please enter a question")

# Tab 2: Cost Estimation
with tab2:
    st.header("AWS Cost Estimation")
    st.markdown("""
    Estimate your monthly infrastructure costs. Leave fields empty to skip that resource type.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("EC2 Instances")
        ec2_count = st.number_input("Number of Instances", min_value=0, max_value=100, value=0, key="ec2_count")
        ec2_type = st.selectbox(
            "Instance Type",
            ["t3.micro", "t3.small", "t3.medium", "t3.large", "m5.large", "c5.large"],
            key="ec2_type"
        )
    
    with col2:
        st.subheader("RDS Databases")
        rds_count = st.number_input("Number of Instances", min_value=0, max_value=10, value=0, key="rds_count")
        rds_type = st.selectbox(
            "Instance Type",
            ["db.t3.micro", "db.t3.small", "db.m5.large"],
            key="rds_type"
        )
    
    with col3:
        st.subheader("Storage")
        s3_gb = st.number_input("S3 Storage (GB)", min_value=0, max_value=10000, value=0, key="s3_gb")
    
    if st.button("Calculate Cost", key="cost_btn", type="primary", use_container_width=True):
        infrastructure = {}
        if ec2_count > 0:
            infrastructure["ec2_instances"] = [{"type": ec2_type, "count": int(ec2_count)}]
        if rds_count > 0:
            infrastructure["rds_instances"] = [{"type": rds_type, "count": int(rds_count)}]
        if s3_gb > 0:
            infrastructure["s3_storage_gb"] = int(s3_gb)
        
        if infrastructure:
            with st.spinner("Calculating costs..."):
                estimate = CostEstimator.estimate_monthly_cost(infrastructure)
                
                # Display total
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Monthly Cost",
                        f"${estimate['estimated_monthly_cost']:.2f}",
                        delta="Per month"
                    )
                with col2:
                    st.metric("Annual Cost", f"${estimate['estimated_monthly_cost'] * 12:.2f}")
                with col3:
                    st.metric("Number of Services", len(estimate['breakdown']))
                
                # Breakdown
                st.subheader("Cost Breakdown")
                for service, cost in estimate['breakdown'].items():
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(service)
                        with col2:
                            st.write(f"**${cost:.2f}**")
        else:
            st.info("Please enter infrastructure details")

# Tab 3: Code Generation
with tab3:
    st.header("Infrastructure Code Generation")
    st.markdown("""
    Auto-generate production-ready Terraform code for your infrastructure.
    """)
    
    code_type = st.radio(
        "Code Type",
        ["Terraform", "CloudFormation"],
        horizontal=True
    )
    
    description = st.text_area(
        "Describe your infrastructure needs",
        placeholder="e.g., 3-tier web app with auto-scaling, RDS database, load balancer",
        height=100
    )
    
    if st.button("Generate Code", key="code_btn", type="primary", use_container_width=True):
        if description:
            with st.spinner("Generating code..."):
                result = predict(
                    f"Generate {code_type} code for: {description}",
                    features={"generate_code": True}
                )
                
                if code_type == "Terraform":
                    code = result.get('terraform_code', 'No code generated')
                    language = "hcl"
                else:
                    code = result.get('cloudformation_code', 'No code generated')
                    language = "json"
                
                st.code(code, language=language)
                
                # Copy button
                st.button("📋 Copy Code", key="copy_btn")
        else:
            st.warning("Please describe your infrastructure")

# Tab 4: Architecture Diagrams
with tab4:
    st.header("Architecture Diagrams")
    st.markdown("""
    Generate and visualize different architecture patterns.
    """)
    
    diagram_type = st.radio(
        "Select Architecture Pattern",
        ["Microservices", "Serverless", "Kubernetes"],
        horizontal=True
    )
    
    if st.button("Generate Diagram", key="diagram_btn", type="primary", use_container_width=True):
        with st.spinner("Generating diagram..."):
            result = predict(
                f"Show {diagram_type.lower()} architecture",
                features={
                    "architecture_diagram": True,
                    "diagram_type": diagram_type.lower()
                }
            )
            
            diagram_code = result.get('architecture_diagram', '')
            
            if diagram_code:
                # Display as code (Mermaid format)
                st.code(diagram_code, language="markdown")
                
                st.info("""
                💡 **Tip**: Copy this Mermaid diagram code and paste it into:
                - GitHub markdown files
                - Notion
                - Miro
                - Any Mermaid renderer
                """)
            else:
                st.warning("Could not generate diagram")

# Tab 5: Security Audit
with tab5:
    st.header("Security Audit")
    st.markdown("""
    Perform a security assessment of your infrastructure configuration.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        encryption = st.checkbox("Encryption at Rest Enabled", value=False)
    with col2:
        mfa = st.checkbox("MFA Enabled", value=False)
    with col3:
        security_groups = st.checkbox("Security Groups Restricted", value=False)
    
    additional_config = st.text_area(
        "Additional Configuration (optional)",
        placeholder="e.g., Using AWS WAF, GuardDuty enabled, VPC endpoint restrictions",
        height=80
    )
    
    if st.button("Run Security Audit", key="audit_btn", type="primary", use_container_width=True):
        with st.spinner("Running security audit..."):
            infrastructure = {
                "encryption_enabled": encryption,
                "mfa_enabled": mfa,
                "restrict_security_groups": security_groups
            }
            if additional_config:
                infrastructure["additional_config"] = additional_config
            
            result = predict(
                "Perform security audit",
                context=infrastructure,
                features={"security_scan": True}
            )
            
            audit = result.get('security_audit', {})
            
            # Display score
            score = audit.get('score', 0)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Security Score", f"{score}%")
            with col2:
                st.metric("Passed Checks", len(audit.get('passed', [])))
            with col3:
                st.metric("Failed Checks", len(audit.get('failed', [])))
            
            # Passed checks
            if audit.get('passed'):
                st.success(f"✅ **Passed Checks ({len(audit['passed'])})**")
                for check in audit['passed']:
                    st.write(f"- {check}")
            
            # Failed checks
            if audit.get('failed'):
                st.error(f"❌ **Failed Checks ({len(audit['failed'])})**")
                for check in audit['failed']:
                    st.write(f"- {check}")
            
            # Recommendations
            if audit.get('recommendations'):
                st.warning("💡 **Recommendations**")
                for rec in audit['recommendations']:
                    st.write(f"- {rec}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p><b>UP2CLOUD AI Cloud Engineering Assistant</b></p>
    <p>Model Version 2.0.0 Premium | Production Ready ✅</p>
    <p><a href='https://up2cloud.com'>Website</a> • <a href='mailto:info@up2cloud.com'>Contact</a></p>
</div>
""", unsafe_allow_html=True)
