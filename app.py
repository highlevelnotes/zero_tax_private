# app.py
import os
import pandas as pd
import streamlit as st

# 로컬 모듈
import db

st.set_page_config(page_title="Sheet-like CRUD (분리구조)", layout="wide")

def load_df() -> pd.DataFrame:
    data = db.fetch_all()
    return pd.DataFrame(data, columns=["id", "name", "qty", "price", "note"])

def main():
    st.title("Streamlit + SQLite (분리): 구글시트 느낌 CRUD")

    # DB 초기화 버튼
    cols = st.columns(3)
    with cols[0]:
        if st.button("DB 초기화(스키마+데모)"):
            db.init_db()
            st.success("DB 초기화 완료")
            st.rerun()
    with cols[1]:
        st.caption(f"DB 파일: {os.environ.get('APP_DB_PATH', 'app.db')}")

    df = load_df()
    st.caption("아래 테이블은 직접 편집 가능. 행 추가/삭제 후 '변경 적용'으로 커밋.")
    edited_df = st.data_editor(
        df,
        key="sheet",
        num_rows="dynamic",  # 행 추가/삭제 허용
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("상품명", required=True),
            "qty": st.column_config.NumberColumn("수량", min_value=0, step=1),
            "price": st.column_config.NumberColumn("가격", min_value=0.0, step=0.1, format="%.2f"),
            "note": st.column_config.TextColumn("메모"),
        },
    )

    changes = st.session_state.get("sheet", {})
    edited_rows = changes.get("edited_rows", {})    # {row_idx: {col: new_value}}
    added_rows = changes.get("added_rows", [])      # [ {col: val, ...}, ... ]
    deleted_rows = changes.get("deleted_rows", [])  # [row_idx, row_idx, ...]

    with st.expander("변경 로그", expanded=False):
        st.json(changes)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("변경 적용(Commit)"):
            # 화면 인덱스 -> id 매핑
            idx_to_id = df["id"].reset_index().set_index("index")["id"].to_dict()

            # 업데이트
            update_payload = []
            for idx_str, changed in edited_rows.items():
                idx = int(idx_str)
                row_id = int(idx_to_id[idx])
                update_payload.append((row_id, changed))
            if update_payload:
                db.update_rows(update_payload)

            # 추가
            if added_rows:
                db.insert_rows(added_rows)

            # 삭제
            if deleted_rows:
                del_ids = [int(idx_to_id[int(i)]) for i in deleted_rows]
                db.delete_by_ids(del_ids)

            # 변경 로그 초기화
            st.session_state["sheet"]["edited_rows"] = {}
            st.session_state["sheet"]["added_rows"] = []
            st.session_state["sheet"]["deleted_rows"] = []
            st.success("DB에 변경사항을 반영했습니다.")
            st.rerun()

    with c2:
        if st.button("새로고침"):
            st.rerun()

    # 간단 리포트
    st.subheader("요약")
    st.write(f"총 품목 수: {len(edited_df)}")
    st.write(f"총 수량: {int(edited_df['qty'].fillna(0).sum())}")
    st.write(f"재고 평가액: {float((edited_df['qty'].fillna(0) * edited_df['price'].fillna(0.0)).sum()):.2f}")

if __name__ == "__main__":
    # 첫 실행에 DB 없으면 자동 초기화
    if not os.path.exists(os.environ.get("APP_DB_PATH", "app.db")):
        db.init_db()
    main()
