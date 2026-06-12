"""
TurboShare — Self-signed SSL certificate generator.

Generates a fresh RSA-2048 certificate at every session start so all
traffic is HTTPS-encrypted even on shared networks.  The certificate
includes the local IP as a SAN (Subject Alternative Name) which is
required by modern mobile browsers.
"""

import ssl
import tempfile
import datetime
from pathlib import Path
from ipaddress import IPv4Address

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_self_signed_cert(
    ip_address: str,
    valid_hours: int = 24,
) -> tuple[Path, Path, ssl.SSLContext]:
    """Create a self-signed TLS certificate for *ip_address*.

    Returns ``(cert_path, key_path, ssl_context)`` where the files are
    written to a secure temp directory and the ``SSLContext`` is ready
    to hand to aiohttp.
    """
    # ── Key pair ────────────────────────────────────────────────────
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # ── Certificate builder ─────────────────────────────────────────
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, f"TurboShare ({ip_address})"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "TurboShare"),
    ])

    now = datetime.datetime.now(datetime.timezone.utc)

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(hours=valid_hours))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.IPAddress(IPv4Address(ip_address)),
            ]),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    # ── Write to temp files ─────────────────────────────────────────
    tmp_dir = Path(tempfile.mkdtemp(prefix="turboshare_ssl_"))

    cert_path = tmp_dir / "cert.pem"
    key_path = tmp_dir / "key.pem"

    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )

    # ── SSLContext ──────────────────────────────────────────────────
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(cert_path), str(key_path))
    # Allow self-signed (the client will need to accept manually)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    return cert_path, key_path, ctx
