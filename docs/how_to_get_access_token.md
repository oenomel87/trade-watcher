# 한국투자증권 Open API - 접근토큰 발급 가이드

## 기본 정보

| 항목 | 내용 |
|------|------|
| API 통신방식 | REST |
| 메뉴 위치 | OAuth인증 |
| API 명 | 접근토큰발급(P) |
| API ID | 인증-001 |
| HTTP Method | POST |

## 엔드포인트

### 실전 환경
- **Domain**: `https://openapi.koreainvestment.com:9443`
- **URL**: `/oauth2/tokenP`
- **전체 경로**: `https://openapi.koreainvestment.com:9443/oauth2/tokenP`

### 모의 환경
- **Domain**: `https://openapivts.koreainvestment.com:29443`
- **URL**: `/oauth2/tokenP`
- **전체 경로**: `https://openapivts.koreainvestment.com:29443/oauth2/tokenP`

## 개요

본인 계좌에 필요한 인증 절차로, 인증을 통해 접근 토큰을 부여받아 오픈API 활용이 가능합니다.

### 주요 특징

1. **접근토큰(access_token)의 유효기간은 24시간**이며 (1일 1회 발급 원칙)
   - 갱신 발급 주기는 6시간입니다
   - 6시간 이내는 기존 발급키로 응답

2. 접근토큰발급(/oauth2/tokenP) 시 **접근토큰값(access_token)**과 함께 수신되는 **접근토큰 유효기간(access_token_token_expired)**을 이용해 접근토큰을 관리할 수 있습니다

### ⚠️ 중요 사항

'23.4.28 이후 지나치게 잦은 토큰 발급 요청건을 제어하기 위해 **신규 접근토큰 발급 이후 일정시간(6시간) 이내에 재호출 시에는 직전 토큰값을 리턴**하게 되었습니다.

일정시간 이후 접근토큰발급 API 호출 시에는 신규 토큰값을 리턴합니다.

## Request

### Request Body

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| grant_type | 권한부여 Type | string | Y | 18 | `client_credentials` (고정값) |
| appkey | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey<br/>**⚠️ 절대 노출되지 않도록 주의** |
| appsecret | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret<br/>**⚠️ 절대 노출되지 않도록 주의** |

### Request Example (Python)

```python
import requests
import json

url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"

data = {
    "grant_type": "client_credentials",
    "appkey": "PSg5dctL9dKPo727J13Ur405OSXXXXXXXXXX",
    "appsecret": "yo2t8zS68zpdjGuWvFyM9VikjXE0i0CbgPEamnqPA00G0bIfrdfQb2RUD1xP7SqatQXr1cD1fGUNsb78MMXoq6o4lAYt9YTtHAjbMoFy+c72kbq5owQY1Pvp39/x6ejpJlXCj7gE3yVOB/h25Hvl+URmYeBTfrQeOqIAOYc/OIXXXXXXXXXX"
}

response = requests.post(url, json=data)
token_data = response.json()
```

## Response

### Response Body

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| access_token | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token<br/><br/>**일반개인고객/일반법인고객:**<br/>- Access token 유효기간: 1일<br/>- 일정시간(6시간) 이내에 재호출 시 직전 토큰값 리턴<br/>- OAuth 2.0의 Client Credentials Grant 절차 준용<br/><br/>**제휴법인:**<br/>- Access token 유효기간: 3개월<br/>- Refresh token 유효기간: 1년<br/>- OAuth 2.0의 Authorization Code Grant 절차 준용 |
| token_type | 접근토큰유형 | string | Y | 20 | 접근토큰유형: `Bearer`<br/>※ API 호출 시, 접근토큰유형 "Bearer" 입력<br/>예: `Bearer eyJ....` |
| expires_in | 접근토큰 유효기간 | number | Y | 10 | 유효기간(초)<br/>예: `86400` (24시간) |
| access_token_token_expired | 접근토큰 유효기간(일시표시) | string | Y | 50 | 유효기간(년:월:일 시:분:초)<br/>예: `2023-12-22 08:16:59` |

### Response Example

```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6ImMwNzM1NTYzLTA1MjctNDNhZS05ODRiLTJiNWI1ZWZmOWYyMyIsImlzcyI6InVub2d3IiwiZXhwIjoxNjQ5NzUxMTAwLCJpYXQiOjE2NDE5NzUxMDAsImp0aSI6IkJTZlM0QUtSSnpRVGpmdHRtdXZlenVQUTlKajc3cHZGdjBZVyJ9.Oyt_C639yUjWmRhymlszgt6jDo8fvIKkkxH1mMngunV1T15SCC4I3Xe6MXxcY23DXunzBfR1uI0KXXXXXXXXXX",
    "access_token_token_expired": "2023-12-22 08:16:59",
    "token_type": "Bearer",
    "expires_in": 86400
}
```

## 사용 방법

### 1. 토큰 발급

```python
import requests

def get_access_token(appkey, appsecret, is_real=True):
    """
    한국투자증권 API 접근 토큰 발급
    
    Args:
        appkey: 한국투자증권에서 발급받은 앱키
        appsecret: 한국투자증권에서 발급받은 앱시크릿키
        is_real: True=실전, False=모의
    
    Returns:
        dict: 토큰 정보 (access_token, token_type, expires_in, access_token_token_expired)
    """
    if is_real:
        url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
    else:
        url = "https://openapivts.koreainvestment.com:29443/oauth2/tokenP"
    
    data = {
        "grant_type": "client_credentials",
        "appkey": appkey,
        "appsecret": appsecret
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 사용 예시
token_info = get_access_token("YOUR_APPKEY", "YOUR_APPSECRET", is_real=False)
access_token = token_info["access_token"]
```

### 2. API 호출 시 토큰 사용

```python
import requests

def call_api_with_token(access_token, appkey, appsecret):
    """
    발급받은 토큰으로 API 호출
    """
    url = "https://openapi.koreainvestment.com:9443/your/api/endpoint"
    
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appkey": appkey,
        "appsecret": appsecret
    }
    
    response = requests.get(url, headers=headers)
    return response.json()
```

### 3. 토큰 관리 팁

```python
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, appkey, appsecret, is_real=True):
        self.appkey = appkey
        self.appsecret = appsecret
        self.is_real = is_real
        self.access_token = None
        self.token_expired = None
    
    def get_token(self):
        """토큰이 만료되었거나 없으면 새로 발급, 아니면 기존 토큰 반환"""
        if self.access_token is None or self._is_token_expired():
            self._refresh_token()
        return self.access_token
    
    def _is_token_expired(self):
        """토큰 만료 여부 확인 (만료 30분 전에 갱신)"""
        if self.token_expired is None:
            return True
        
        expired_time = datetime.strptime(self.token_expired, "%Y-%m-%d %H:%M:%S")
        buffer_time = timedelta(minutes=30)
        
        return datetime.now() >= (expired_time - buffer_time)
    
    def _refresh_token(self):
        """토큰 새로 발급"""
        token_info = get_access_token(self.appkey, self.appsecret, self.is_real)
        self.access_token = token_info["access_token"]
        self.token_expired = token_info["access_token_token_expired"]
```

## 주의사항

1. **보안**: appkey와 appsecret은 절대 GitHub 등 공개 저장소에 노출하지 마세요
2. **토큰 재사용**: 6시간 이내 재호출 시 동일한 토큰이 반환되므로, 토큰을 캐싱해서 사용하는 것이 좋습니다
3. **유효기간 관리**: `access_token_token_expired` 값을 확인하여 토큰 만료 전에 미리 갱신하세요
4. **API 호출**: 모든 API 호출 시 헤더에 `Bearer {access_token}` 형식으로 토큰을 포함해야 합니다