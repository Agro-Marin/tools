queries = [
    """ALTER TABLE account_account DROP CONSTRAINT "account_account_asset_model_fkey";""",
    """ALTER TABLE account_account ADD  CONSTRAINT "account_account_asset_model_fkey" FOREIGN KEY ("asset_model") REFERENCES "public"."account_asset" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    
    """ALTER TABLE account_asset DROP CONSTRAINT "account_asset_model_id_fkey";""",
    """ALTER TABLE account_asset ADD  CONSTRAINT "account_asset_model_id_fkey" FOREIGN KEY ("model_id") REFERENCES "public"."account_asset" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    
    """ALTER TABLE account_move DROP CONSTRAINT "account_move_asset_id_fkey";""",
    """ALTER TABLE account_move ADD  CONSTRAINT "account_move_asset_id_fkey" FOREIGN KEY ("asset_id") REFERENCES "public"."account_asset" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
    
    """ALTER TABLE asset_move_line_rel DROP CONSTRAINT "asset_move_line_rel_asset_id_fkey";""",
    """ALTER TABLE asset_move_line_rel ADD  CONSTRAINT "asset_move_line_rel_asset_id_fkey" FOREIGN KEY ("asset_id") REFERENCES "public"."account_asset" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

    """DELETE FROM ir_model_data WHERE module='marin' AND model='account.asset'""",
]