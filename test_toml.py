from datetime import date
from carbon_txt.schemas.common import Upstream, Service
from carbon_txt.schemas.version_0_4 import CarbonTxtFile, Organisation, Disclosure

f = CarbonTxtFile(
    org=Organisation(
        disclosures=[
            Disclosure(
                url="https://example.com/sustainability", doc_type="sustainability-page"
            ),
            Disclosure(url="https://example.com/page", doc_type="web-page"),
        ]
    ),
    upstream=Upstream(
        services=[
            Service(
                domain="https://example.com", service_type="virtual-private-servers"
            )
        ]
    ),
    version="0.4",
    last_updated=date.today(),
)

print(f.to_toml())
