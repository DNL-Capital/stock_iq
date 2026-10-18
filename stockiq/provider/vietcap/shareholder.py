import pandas as pd

from ...core._http import NET
from ...core.constants import (
    IQ_URL,
    make_headers,
)
from ...core.exceptions import wrap_errors
from ...core.utils import to_day


class stock_shareholder:
    def __init__(self, symbol: str):
        """Truy vấn dữ liệu cổ đông cho một mã. / Shareholder accessor."""
        self.symbol = symbol

    # Thông tin cổ đông
    @wrap_errors("Không lấy được dữ liệu cho '{self.symbol}': {error}")
    def shareholders_info(self) -> pd.DataFrame:
        """Danh sách cổ đông lớn. / Major shareholders.

        Returns:
            pd.DataFrame cổ đông lớn / major shareholders.
        """
        headers = make_headers()

        url1 = f"{IQ_URL}/company/{self.symbol.upper()}/shareholder"
        response = NET.get(url1, headers=headers)
        data1 = response.json()["data"]
        data1 = pd.json_normalize(data1)
        data1 = data1.drop(columns=["ownerNameEn", "ownerCode", "positionNameEn"])
        data1["percentage"] = round(data1["percentage"] * 100, 4)
        data1["updateDate"] = to_day(data1["updateDate"])
        data1["publicDate"] = to_day(data1["publicDate"])
        data1["ownerType"] = data1["ownerType"].replace(
            {"INDIVIDUAL": "individual", "CORPORATE": "corporate"}
        )
        data1["symbol"] = self.symbol.upper()
        col = data1.pop("symbol")
        data1.insert(0, "symbol", col)
        data1["positionName"] = data1["positionName"].fillna("-")
        data1 = data1.sort_values("updateDate", ascending=True).reset_index(
            drop=True
        )
        return data1

    # Cấu trúc cổ đông
    @wrap_errors("Không lấy được dữ liệu cho '{self.symbol}': {error}")
    def shareholders_structure(self) -> pd.DataFrame:
        """Cơ cấu sở hữu. / Ownership structure.

        Returns:
            pd.DataFrame cơ cấu sở hữu / ownership structure.
        """
        headers = make_headers()

        url2 = f"{IQ_URL}/company/{self.symbol.upper()}/shareholder-structure"
        response = NET.get(url2, headers=headers)
        data2 = response.json()["data"]
        data2 = pd.json_normalize(data2)
        percent_cols = [
            "statePercentage",
            "foreignPercentage",
            "otherPercentage",
            "bodPercentage",
            "institutionPercentage",
        ]
        data2[percent_cols] = round(data2[percent_cols] * 100, 4)
        data2["totalShares"] = data2["totalShares"].astype(int)
        data2["symbol"] = self.symbol.upper()
        col = data2.pop("symbol")
        data2.insert(0, "symbol", col)
        data2 = data2[
            [
                "symbol",
                "totalShares",
                "stateVolume",
                "statePercentage",
                "foreignerVolume",
                "foreignPercentage",
                "otherVolume",
                "otherPercentage",
                "bodPercentage",
                "institutionPercentage",
            ]
        ]
        data2.rename(
            columns={
                "statePercentage": "statePct",
                "foreignPercentage": "foreignPct",
                "otherPercentage": "otherPct",
                "foreignerVolume": "foreignerVol",
                "otherVolume": "otherVol",
                "stateVolume": "stateVol",
                "bodPercentage": "bodPct",
                "institutionPercentage": "institutionPct",
            },
            inplace=True,
        )
        return data2

    # Công ty liên quan
    @wrap_errors("Không lấy được dữ liệu cho '{self.symbol}': {error}")
    def shareholders_relationship(self) -> pd.DataFrame:
        """Công ty liên kết & công ty con. / Affiliates & subsidiaries.

        Returns:
            pd.DataFrame quan hệ công ty / related companies.
        """
        headers = make_headers()

        url3 = f"{IQ_URL}/company/{self.symbol.upper()}/relationship"
        response = NET.get(url3, headers=headers)
        data3_1 = response.json()["data"]["affiliates"]
        data3_1 = pd.json_normalize(data3_1)
        data3_1["organType"] = "associate"
        data3_2 = response.json()["data"]["subsidiaries"]
        data3_2 = pd.json_normalize(data3_2)
        data3_2["organType"] = "subsidiary"
        data3 = pd.concat([data3_1, data3_2], ignore_index=True)
        data3 = data3.drop(
            columns=["rightOrganCode", "rightTicker", "rightOrganNameEn"]
        )
        data3["ownedPercentage"] = round(data3["ownedPercentage"] * 100, 4)
        data3["ownedQuantity"] = data3["ownedQuantity"].astype(int)
        data3["symbol"] = self.symbol.upper()
        col = data3.pop("symbol")
        data3.insert(0, "symbol", col)
        data3.rename(
            columns={
                "ownedPercentage": "ownedPct",
                "rightOrganNameVi": "companyName",
            },
            inplace=True,
        )
        return data3[
            ["symbol", "companyName", "organType", "ownedQuantity", "ownedPct"]
        ]

    # Giao dịch nội bộ
    @wrap_errors("Không lấy được dữ liệu cho '{self.symbol}': {error}")
    def insider_trans(self) -> pd.DataFrame:
        """Giao dịch nội bộ. / Insider transactions.

        Returns:
            pd.DataFrame giao dịch nội bộ / insider trades.
        """
        headers = make_headers()
        url = f"{IQ_URL}/company/{self.symbol.upper()}/insider-transaction?page=0&size=1000"
        response = NET.get(url, headers=headers)
        data = pd.json_normalize(response.json()["data"]["content"])
        data["symbol"] = self.symbol.upper()
        col = data.pop("symbol")
        data.insert(0, "symbol", col)
        data["traderNameVi"] = data["traderNameVi"].fillna(
            data["traderOrganNameVi"]
        )
        nacol = ["traderPositionVi", "relativeNameVi", "roleNameVi"]
        data[nacol] = data[nacol].fillna("-")
        for col in [
            "shareRegister",
            "shareBeforeTrade",
            "shareAcquire",
            "shareAfterTrade",
        ]:
            data[col] = pd.to_numeric(data[col], errors="coerce").astype("Int64")

        data = data.drop(
            columns=[
                "id",
                "organCode",
                "eventNameEn",
                "ticker",
                "eventCode",
                "sourceUrlVi",
                "sourceUrlEn",
                "tradeStatusEn",
                "traderPersonId",
                "traderNameEn",
                "traderPositionEn",
                "actionTypeCode",
                "actionTypeEn",
                "relativeNameEn",
                "icbCodeLv1",
                "traderOrganNameEn",
                "displayDate1",
                "displayDate2",
                "roleNameEn",
                "traderOrganNameVi",
            ]
        )
        data["eventNameVi"] = data["eventNameVi"].replace(
            r"^Giao dịch nội bộ: ", "", regex=True
        )
        ngay = ["startDate", "endDate", "publicDate"]
        for col in ngay:
            data[col] = to_day(data[col])
        data["ownershipAfterTrade"] = data["ownershipAfterTrade"] * 100
        chucvu = self.shareholders_info()[["ownerName", "positionName"]]
        data = pd.merge(
            data, chucvu, left_on="relativeNameVi", right_on="ownerName", how="left"
        )
        data = data.drop(columns=["ownerName"])
        mask = data["eventNameVi"] != "Giao dịch người liên quan"
        data.loc[mask, ["relativeNameVi", "positionName", "roleNameVi"]] = "-"
        filted_cols = [
            "symbol",
            "eventNameVi",
            "traderNameVi",
            "traderPositionVi",
            "actionTypeVi",
            "tradeStatusVi",
            "shareRegister",
            "shareBeforeTrade",
            "shareAcquire",
            "shareAfterTrade",
            "ownershipAfterTrade",
            "startDate",
            "endDate",
            "publicDate",
            "relativeNameVi",
            "positionName",
            "roleNameVi",
        ]
        df = data[filted_cols]
        df = df.rename(
            columns={
                "eventNameVi": "eventType",
                "traderNameVi": "traderName",
                "traderPositionVi": "position",
                "actionTypeVi": "actionType",
                "tradeStatusVi": "tradeStatus",
                "shareRegister": "registeredShares",
                "shareBeforeTrade": "sharesBeforeTrade",
                "shareAcquire": "shareChange",
                "shareAfterTrade": "sharesAfterTrade",
                "ownershipAfterTrade": "ownershipAfterTradePct",
                "relativeNameVi": "relatedPerson",
                "roleNameVi": "relationship",
                "positionName": "relatedPersonPosition",
            }
        )

        df = df.sort_values(
            ["publicDate", "startDate", "endDate"], ascending=[True, True, True]
        ).reset_index(drop=True)
        return df
