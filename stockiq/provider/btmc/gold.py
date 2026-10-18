import pandas as pd

from ...core._http import NET
from ...core.constants import BTMC_KEY, BTMC_URL, USER_AGENT
from ...core.exceptions import wrap_errors


class btmc_gold:
    @staticmethod
    @wrap_errors()
    def prices() -> pd.DataFrame:
        """Giá vàng/bạc Bảo Tín Minh Châu hiện tại. / Current Bao Tin Minh Chau gold and silver prices.

        Returns:
            pd.DataFrame giá mua/bán từng loại, sắp xếp giá bán giảm dần / buy and sell price per product (latest update).
        """
        url = f"{BTMC_URL}/getpricebtmc"
        response = NET.get(
            url, params={"key": BTMC_KEY}, headers={"user-agent": USER_AGENT}
        )
        rows = response.json()["DataList"]["Data"]

        # Mỗi dòng đánh số trong khóa: "@n_1", "@pb_1", ... / keys carry the row number.
        data = pd.DataFrame(
            [
                {
                    "name": row.get(f"@n_{row['@row']}", ""),
                    "karat": row.get(f"@k_{row['@row']}", ""),
                    "goldContent": row.get(f"@h_{row['@row']}", ""),
                    "buyPrice": row.get(f"@pb_{row['@row']}"),
                    "sellPrice": row.get(f"@ps_{row['@row']}"),
                    "worldPrice": row.get(f"@pt_{row['@row']}"),
                    "time": row.get(f"@d_{row['@row']}"),
                }
                for row in rows
            ]
        )
        for col in ["buyPrice", "sellPrice", "worldPrice"]:
            data[col] = pd.to_numeric(data[col], errors="coerce")
        data["time"] = pd.to_datetime(
            data["time"], format="%d/%m/%Y %H:%M", errors="coerce"
        )
        # API trả mọi lần cập nhật trong ngày; chỉ giữ lần mới nhất của mỗi sản phẩm.
        data = data.sort_values("time").drop_duplicates(
            ["name", "karat", "goldContent"], keep="last"
        )
        return data.sort_values("sellPrice", ascending=False).reset_index(drop=True)
