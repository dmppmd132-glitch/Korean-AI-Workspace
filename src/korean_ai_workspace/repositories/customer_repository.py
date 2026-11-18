from __future__ import annotations

from sqlalchemy import or_, select, update

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import Customer, GlossaryTerm


class CustomerRepository:
    def __init__(self, database: Database):
        self.database = database

    def add(self, **values) -> Customer:
        company_name = values.get("company_name", "").strip()
        if not company_name:
            raise ValueError("公司名稱不可為空白")
        values["company_name"] = company_name
        record = Customer(**values)
        with self.database.session() as session:
            session.add(record); session.flush(); session.refresh(record)
        return record

    def update(self, customer_id: int, **values) -> Customer:
        with self.database.session() as session:
            record = session.get(Customer, customer_id)
            if record is None:
                raise ValueError("找不到指定客戶")
            company_name = values.get("company_name", record.company_name).strip()
            if not company_name:
                raise ValueError("公司名稱不可為空白")
            values["company_name"] = company_name
            for key, value in values.items():
                if hasattr(record, key): setattr(record, key, value)
            session.flush(); session.refresh(record)
            return record

    def get(self, customer_id: int) -> Customer | None:
        with self.database.session() as session:
            return session.get(Customer, customer_id)

    def search(self, keyword: str = "", limit: int = 200) -> list[Customer]:
        statement = select(Customer).order_by(Customer.company_name.asc()).limit(limit)
        value = keyword.strip()
        if value:
            pattern = f"%{value}%"
            statement = statement.where(or_(Customer.company_name.like(pattern), Customer.korean_company_name.like(pattern), Customer.contact_name.like(pattern), Customer.email.like(pattern), Customer.industry.like(pattern)))
        with self.database.session() as session:
            return list(session.scalars(statement))

    def delete(self, customer_id: int) -> None:
        with self.database.session() as session:
            session.execute(update(GlossaryTerm).where(GlossaryTerm.customer_id == customer_id).values(customer_id=None))
            record = session.get(Customer, customer_id)
            if record is not None:
                session.delete(record)
