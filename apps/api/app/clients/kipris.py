from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree


WORD_SEARCH_URL = (
    "http://plus.kipris.or.kr/kipo-api/kipi/"
    "patUtiModInfoSearchSevice/getWordSearch"
)
CLAIM_INFO_URL = (
    "http://plus.kipris.or.kr/openapi/rest/"
    "patUtiModInfoSearchSevice/patentClaimInfo"
)


@dataclass(frozen=True)
class PatentSearchResult:
    application_number: str
    title: str
    abstract: str | None = None
    applicant_name: str | None = None
    ipc_number: str | None = None
    application_date: str | None = None
    register_status: str | None = None
    register_number: str | None = None
    publication_number: str | None = None
    open_number: str | None = None


@dataclass(frozen=True)
class ClaimInfoResult:
    application_number: str
    claims: list[str]
    result_code: str | None
    result_message: str | None


class KiprisClient:
    def __init__(self, api_key: str, timeout: float = 20.0) -> None:
        if not api_key:
            raise ValueError("KIPRIS API key is required.")
        self.api_key = api_key
        self.timeout = timeout

    def search_patents(self, keyword: str, limit: int = 10, page_no: int = 1) -> list[PatentSearchResult]:
        params = {
            "word": keyword,
            "year": "0",
            "patent": "true",
            "utility": "true",
            "numOfRows": str(limit),
            "pageNo": str(page_no),
            "ServiceKey": self.api_key,
        }
        root = self._get_xml(WORD_SEARCH_URL, params)
        self._raise_if_error(root)

        items = root.findall("./body/items/item")
        results: list[PatentSearchResult] = []
        for item in items:
            application_number = _text(item, "applicationNumber")
            title = _text(item, "inventionTitle")
            if not application_number or not title:
                continue
            results.append(
                PatentSearchResult(
                    application_number=application_number,
                    title=title,
                    abstract=_optional_text(item, "astrtCont"),
                    applicant_name=_optional_text(item, "applicantName"),
                    ipc_number=_optional_text(item, "ipcNumber"),
                    application_date=_optional_text(item, "applicationDate"),
                    register_status=_optional_text(item, "registerStatus"),
                    register_number=_optional_text(item, "registerNumber"),
                    publication_number=_optional_text(item, "publicationNumber"),
                    open_number=_optional_text(item, "openNumber"),
                )
            )
        return results

    def get_claims(self, application_number: str) -> ClaimInfoResult:
        params = {
            "applicationNumber": application_number,
            "accessKey": self.api_key,
        }
        root = self._get_xml(CLAIM_INFO_URL, params)
        result_code = _optional_text(root, "./header/resultCode")
        result_message = _optional_text(root, "./header/resultMsg")
        self._raise_if_error(root)

        claim_nodes = root.findall("./body/items/claimInfo/claim")
        claims = [_inner_xml(node).strip() for node in claim_nodes if _inner_xml(node).strip()]
        return ClaimInfoResult(
            application_number=application_number,
            claims=claims,
            result_code=result_code,
            result_message=result_message,
        )

    def _get_xml(self, url: str, params: dict[str, str]) -> ElementTree.Element:
        request_url = f"{url}?{urlencode(params)}"
        request = Request(request_url, headers={"User-Agent": "ClaimLens/0.1"})
        with urlopen(request, timeout=self.timeout) as response:
            body = response.read()
        return ElementTree.fromstring(body)

    @staticmethod
    def _raise_if_error(root: ElementTree.Element) -> None:
        result_code = _optional_text(root, "./header/resultCode")
        result_message = _optional_text(root, "./header/resultMsg")
        success_yn = _optional_text(root, "./header/successYN")
        if result_code and result_code not in {"00", "0"}:
            raise RuntimeError(f"KIPRIS API error {result_code}: {result_message}")
        if success_yn and success_yn.upper() == "N":
            raise RuntimeError(f"KIPRIS API failed: {result_message}")


def _text(node: ElementTree.Element, path: str) -> str:
    found = node.find(path)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def _optional_text(node: ElementTree.Element, path: str) -> str | None:
    value = _text(node, path)
    return value or None


def _inner_xml(node: ElementTree.Element) -> str:
    parts: list[str] = []
    if node.text:
        parts.append(node.text)
    for child in list(node):
        parts.append(ElementTree.tostring(child, encoding="unicode"))
    return "".join(parts)

