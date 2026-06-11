from xml.etree import ElementTree

from app.clients.kipris import (
    BIBLIO_DETAIL_URL,
    CLAIM_INFO_URL,
    BIBLIO_DETAIL_ENDPOINT,
    KiprisClient,
)


class FakeKiprisClient(KiprisClient):
    def __init__(self, responses: dict[str, str | Exception]) -> None:
        super().__init__(api_key="test-key")
        self.responses = responses
        self.requested_urls: list[str] = []

    def _get_xml(self, url: str, params: dict[str, str]) -> ElementTree.Element:
        self.requested_urls.append(url)
        assert params
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return ElementTree.fromstring(response)


def test_get_claims_falls_back_to_bibliography_detail_when_claim_endpoint_is_empty() -> None:
    client = FakeKiprisClient(
        responses={
            CLAIM_INFO_URL: """
                <response>
                  <header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header>
                  <body><items /></body>
                </response>
            """,
            BIBLIO_DETAIL_URL: """
                <response>
                  <header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header>
                  <body>
                    <item>
                      <claimInfoArray>
                        <claimInfo><claim>1. 입력수단; 처리수단</claim></claimInfo>
                      </claimInfoArray>
                    </item>
                  </body>
                </response>
            """,
        }
    )

    result = client.get_claims("10-2024-0000001")

    assert client.requested_urls == [CLAIM_INFO_URL, BIBLIO_DETAIL_URL]
    assert result.source_endpoint == BIBLIO_DETAIL_ENDPOINT
    assert result.source_document_type == "bibliography_detail"
    assert result.claims == ["1. 입력수단; 처리수단"]


def test_get_claims_falls_back_to_bibliography_detail_when_claim_endpoint_fails() -> None:
    client = FakeKiprisClient(
        responses={
            CLAIM_INFO_URL: RuntimeError("KIPRIS claim endpoint failed"),
            BIBLIO_DETAIL_URL: """
                <response>
                  <header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header>
                  <body>
                    <item>
                      <claimInfoArray>
                        <claimInfo><claim>1. 저장수단; 검색수단</claim></claimInfo>
                      </claimInfoArray>
                    </item>
                  </body>
                </response>
            """,
        }
    )

    result = client.get_claims("10-2024-0000001")

    assert client.requested_urls == [CLAIM_INFO_URL, BIBLIO_DETAIL_URL]
    assert result.source_endpoint == BIBLIO_DETAIL_ENDPOINT
    assert result.claims == ["1. 저장수단; 검색수단"]
