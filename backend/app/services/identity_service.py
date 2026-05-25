"""Agent cryptographic identity service — Ed25519 keypairs, signing, SPIFFE-compatible certs."""
import json
from datetime import datetime
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.exceptions import InvalidSignature
from cryptography.x509 import (
    CertificateBuilder, Name, NameAttribute, BasicConstraints,
    random_serial_number,
)
from cryptography.x509.oid import NameOID
import datetime as dt
from sqlalchemy.orm import Session
from loguru import logger
import base64

from app.models.agent_identity import AgentIdentity


class IdentityService:
    """Manages agent cryptographic identities for signed audit trails."""

    def __init__(self, db: Session):
        self.db = db

    def issue_agent_identity(self, agent_id: str) -> AgentIdentity:
        """Generate Ed25519 keypair and issue identity for an agent."""
        self.db.query(AgentIdentity).filter(
            AgentIdentity.agent_id == agent_id,
        ).delete()
        self.db.commit()

        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        spiffe_id = f"spiffe://voise.ai/agent/{agent_id}"
        subject = issuer = Name([
            NameAttribute(NameOID.ORGANIZATION_NAME, "Voise AI"),
            NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Agent Identity"),
            NameAttribute(NameOID.COMMON_NAME, spiffe_id),
        ])
        cert_builder = (
            CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(public_key)
            .serial_number(random_serial_number())
            .not_valid_before(dt.datetime.utcnow())
            .not_valid_after(dt.datetime.utcnow() + dt.timedelta(days=365))
            .add_extension(BasicConstraints(ca=False, path_length=None), critical=True)
        )
        certificate = cert_builder.sign(private_key, None)

        identity = AgentIdentity(
            agent_id=agent_id,
            public_key=public_pem.decode(),
            private_key_encrypted=private_pem.decode(),
            certificate_pem=certificate.public_bytes(Encoding.PEM).decode(),
            spiffe_id=spiffe_id,
            key_version="v1",
        )
        self.db.add(identity)
        self.db.commit()
        self.db.refresh(identity)
        logger.info(f"Issued identity for agent {agent_id} — {spiffe_id}")
        return identity

    def get_identity(self, agent_id: str) -> Optional[AgentIdentity]:
        return self.db.query(AgentIdentity).filter(
            AgentIdentity.agent_id == agent_id,
        ).order_by(AgentIdentity.created_at.desc()).first()

    def rotate_keys(self, agent_id: str) -> Optional[AgentIdentity]:
        old = self.get_identity(agent_id)
        old_version = old.key_version if old else "v0"
        new = self.issue_agent_identity(agent_id)
        new.key_version = f"v{int(old_version[1:] or '0') + 1}"
        self.db.commit()
        logger.info(f"Rotated keys for agent {agent_id} -> {new.key_version}")
        return new

    def sign_action(self, agent_id: str, payload: Dict[str, Any]) -> Optional[str]:
        """Sign payload using Ed25519 private key. Returns base64-encoded signature."""
        identity = self.get_identity(agent_id)
        if not identity:
            logger.warning(f"No active identity for agent {agent_id}")
            return None

        private_key = serialization.load_pem_private_key(
            identity.private_key_encrypted.encode(), password=None,
        )
        if not isinstance(private_key, Ed25519PrivateKey):
            return None

        serialized = json.dumps(payload, sort_keys=True, default=str).encode()
        signature = private_key.sign(serialized)
        b64sig = base64.b64encode(signature).decode()
        return b64sig

    def verify_action(self, agent_id: str, payload: Dict[str, Any], signature: str) -> bool:
        """Verify Ed25519 signature against the agent's public key."""
        identity = self.get_identity(agent_id)
        if not identity:
            return False

        public_key = serialization.load_pem_public_key(identity.public_key.encode())
        if not isinstance(public_key, Ed25519PublicKey):
            return False

        serialized = json.dumps(payload, sort_keys=True, default=str).encode()
        try:
            public_key.verify(base64.b64decode(signature), serialized)
            return True
        except InvalidSignature as e:
            logger.warning(f"verify_action: INVALID signature for agent {agent_id}: {e}")
            return False

    def list_identities(self, organization_id: Optional[str] = None):
        q = self.db.query(AgentIdentity)
        if organization_id:
            q = q.filter(AgentIdentity.organization_id == organization_id)
        return q.order_by(AgentIdentity.created_at.desc()).all()
