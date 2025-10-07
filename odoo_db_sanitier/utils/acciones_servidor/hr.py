queries = [
  
  """ALTER TABLE account_move_line_hr_payslip_line_rel DROP CONSTRAINT "account_move_line_hr_payslip_line_rel_hr_payslip_line_id_fkey";""",
  """ALTER TABLE account_move_line_hr_payslip_line_rel ADD  CONSTRAINT "account_move_line_hr_payslip_line_rel_hr_payslip_line_id_fkey" FOREIGN KEY ("hr_payslip_line_id") REFERENCES "public"."hr_payslip_line" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  
  """ALTER TABLE employee_category_rel DROP CONSTRAINT "employee_category_rel_employee_id_fkey";""",
  """ALTER TABLE employee_category_rel ADD  CONSTRAINT "employee_category_rel_employee_id_fkey" FOREIGN KEY ("employee_id") REFERENCES "public"."hr_employee" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE fleet_vehicle DROP CONSTRAINT "fleet_vehicle_driver_id_fkey";""",
  """ALTER TABLE fleet_vehicle ADD  CONSTRAINT "fleet_vehicle_driver_id_fkey" FOREIGN KEY ("driver_id") REFERENCES "public"."hr_employee" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE fleet_vehicle_assignation_log DROP CONSTRAINT "fleet_vehicle_assignation_log_driver_id_fkey";""",
  """ALTER TABLE fleet_vehicle_assignation_log  ADD CONSTRAINT "fleet_vehicle_assignation_log_driver_id_fkey" FOREIGN KEY ("driver_id") REFERENCES "public"."hr_employee" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE hr_contract DROP CONSTRAINT "hr_contract_structure_type_id_fkey";""",
  """ALTER TABLE hr_contract ADD  CONSTRAINT "hr_contract_structure_type_id_fkey" FOREIGN KEY ("structure_type_id") REFERENCES "public"."hr_payroll_structure_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_contract DROP CONSTRAINT "hr_contract_employee_id_fkey";""",
  """ALTER TABLE hr_contract ADD  CONSTRAINT "hr_contract_employee_id_fkey" FOREIGN KEY ("employee_id") REFERENCES "public"."hr_employee" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_contract DROP CONSTRAINT "hr_contract_job_id_fkey";""",
  """ALTER TABLE hr_contract ADD  CONSTRAINT "hr_contract_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "public"."hr_job" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE hr_employee DROP CONSTRAINT "hr_employee_coach_id_fkey";""",
  """ALTER TABLE hr_employee ADD  CONSTRAINT "hr_employee_coach_id_fkey" FOREIGN KEY ("coach_id") REFERENCES "public"."hr_employee" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_employee DROP CONSTRAINT "hr_employee_contract_id_fkey";""",
  """ALTER TABLE hr_employee ADD  CONSTRAINT "hr_employee_contract_id_fkey" FOREIGN KEY ("contract_id") REFERENCES "public"."hr_contract" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_employee DROP CONSTRAINT "hr_employee_job_id_fkey";""",
  """ALTER TABLE hr_employee ADD  CONSTRAINT "hr_employee_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "public"."hr_job" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_employee DROP CONSTRAINT "hr_employee_leave_manager_id_fkey";""",
  """ALTER TABLE hr_employee ADD  CONSTRAINT "hr_employee_leave_manager_id_fkey" FOREIGN KEY ("leave_manager_id") REFERENCES "public"."res_users" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_employee DROP CONSTRAINT "hr_employee_parent_id_fkey";""",
  """ALTER TABLE hr_employee ADD  CONSTRAINT "hr_employee_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "public"."hr_employee" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_employee DROP CONSTRAINT "hr_employee_resource_calendar_id_fkey";""",
  """ALTER TABLE hr_employee ADD  CONSTRAINT "hr_employee_resource_calendar_id_fkey" FOREIGN KEY ("resource_calendar_id") REFERENCES "public"."resource_calendar" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_employee DROP CONSTRAINT "hr_employee_resource_id_fkey";""",
  """ALTER TABLE hr_employee ADD  CONSTRAINT "hr_employee_resource_id_fkey" FOREIGN KEY ("resource_id") REFERENCES "public"."resource_resource" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  
  """ALTER TABLE hr_payroll_structure_hr_payslip_input_type_rel DROP CONSTRAINT "hr_payroll_structure_hr_payslip_in_hr_payroll_structure_id_fkey";""",
  """ALTER TABLE hr_payroll_structure_hr_payslip_input_type_rel ADD  CONSTRAINT "hr_payroll_structure_hr_payslip_in_hr_payroll_structure_id_fkey" FOREIGN KEY ("hr_payroll_structure_id") REFERENCES "public"."hr_payroll_structure" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  
  """ALTER TABLE hr_payslip DROP CONSTRAINT "hr_payslip_employee_id_fkey";""",
  """ALTER TABLE hr_payslip ADD  CONSTRAINT "hr_payslip_employee_id_fkey" FOREIGN KEY ("employee_id") REFERENCES "public"."hr_employee" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE hr_payslip DROP CONSTRAINT "hr_payslip_contract_id_fkey";""",
  """ALTER TABLE hr_payslip ADD  CONSTRAINT "hr_payslip_contract_id_fkey" FOREIGN KEY ("contract_id") REFERENCES "public"."hr_contract" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_payslip DROP CONSTRAINT "hr_payslip_job_id_fkey";""",
  """ALTER TABLE hr_payslip ADD  CONSTRAINT "hr_payslip_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "public"."hr_job" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_payslip DROP CONSTRAINT "hr_payslip_struct_id_fkey";""",
  """ALTER TABLE hr_payslip ADD  CONSTRAINT "hr_payslip_struct_id_fkey" FOREIGN KEY ("struct_id") REFERENCES "public"."hr_payroll_structure" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_payslip_line DROP CONSTRAINT "hr_payslip_line_salary_rule_id_fkey";""",
  """ALTER TABLE hr_payslip_line ADD  CONSTRAINT "hr_payslip_line_salary_rule_id_fkey" FOREIGN KEY ("salary_rule_id") REFERENCES "public"."hr_salary_rule" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE hr_payslip_line DROP CONSTRAINT "hr_payslip_line_employee_id_fkey";""",
  """ALTER TABLE hr_payslip_line ADD  CONSTRAINT "hr_payslip_line_employee_id_fkey" FOREIGN KEY ("employee_id") REFERENCES "public"."hr_employee" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE hr_payslip_line DROP CONSTRAINT "hr_payslip_line_contract_id_fkey";""",
  """ALTER TABLE hr_payslip_line ADD  CONSTRAINT "hr_payslip_line_contract_id_fkey" FOREIGN KEY ("contract_id") REFERENCES "public"."hr_contract" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE hr_payroll_structure_hr_work_entry_type_rel DROP CONSTRAINT "hr_payroll_structure_hr_work_entry_hr_payroll_structure_id_fkey";""",
  """ALTER TABLE hr_payroll_structure_hr_work_entry_type_rel ADD  CONSTRAINT "hr_payroll_structure_hr_work_entry_hr_payroll_structure_id_fkey" FOREIGN KEY ("hr_payroll_structure_id") REFERENCES "public"."hr_payroll_structure" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  
  """ALTER TABLE hr_payroll_structure DROP CONSTRAINT "hr_payroll_structure_type_id_fkey";""",
  """ALTER TABLE hr_payroll_structure ADD  CONSTRAINT "hr_payroll_structure_type_id_fkey" FOREIGN KEY ("type_id") REFERENCES "public"."hr_payroll_structure_type" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  
  """ALTER TABLE hr_payroll_structure_type DROP CONSTRAINT "hr_payroll_structure_type_default_struct_id_fkey";""",
  """ALTER TABLE hr_payroll_structure_type ADD  CONSTRAINT "hr_payroll_structure_type_default_struct_id_fkey" FOREIGN KEY ("default_struct_id") REFERENCES "public"."hr_payroll_structure" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  
  """ALTER TABLE hr_salary_rule DROP CONSTRAINT "hr_salary_rule_struct_id_fkey";""",
  """ALTER TABLE hr_salary_rule ADD  CONSTRAINT "hr_salary_rule_struct_id_fkey" FOREIGN KEY ("struct_id") REFERENCES "public"."hr_payroll_structure" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  
  """ALTER TABLE hr_recruitment_source DROP CONSTRAINT "hr_recruitment_source_job_id_fkey";""",
  """ALTER TABLE hr_recruitment_source ADD  CONSTRAINT "hr_recruitment_source_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "public"."hr_job" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  
  """ALTER TABLE hr_resume_line DROP CONSTRAINT "hr_resume_line_employee_id_fkey";""",
  """ALTER TABLE hr_resume_line ADD  CONSTRAINT "hr_resume_line_employee_id_fkey" FOREIGN KEY ("employee_id") REFERENCES "public"."hr_employee" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE mrp_workcenter DROP CONSTRAINT "mrp_workcenter_resource_id_fkey";""",
  """ALTER TABLE mrp_workcenter ADD  CONSTRAINT "mrp_workcenter_resource_id_fkey" FOREIGN KEY ("resource_id") REFERENCES "public"."resource_resource" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  
  """ALTER TABLE pos_hr_advanced_employee_hr_employee DROP CONSTRAINT "pos_hr_advanced_employee_hr_employee_hr_employee_id_fkey";""",
  """ALTER TABLE pos_hr_advanced_employee_hr_employee ADD  CONSTRAINT "pos_hr_advanced_employee_hr_employee_hr_employee_id_fkey" FOREIGN KEY ("hr_employee_id") REFERENCES "public"."hr_employee" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  
  """ALTER TABLE pos_hr_basic_employee_hr_employee DROP CONSTRAINT "pos_hr_basic_employee_hr_employee_hr_employee_id_fkey";""",
  """ALTER TABLE pos_hr_basic_employee_hr_employee ADD  CONSTRAINT "pos_hr_basic_employee_hr_employee_hr_employee_id_fkey" FOREIGN KEY ("hr_employee_id") REFERENCES "public"."hr_employee" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  
  """ALTER TABLE pos_order DROP CONSTRAINT "pos_order_employee_id_fkey";""",
  """ALTER TABLE pos_order ADD  CONSTRAINT "pos_order_employee_id_fkey" FOREIGN KEY ("employee_id") REFERENCES "public"."hr_employee" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  
  """ALTER TABLE pos_payment DROP CONSTRAINT "pos_payment_employee_id_fkey";""",
  """ALTER TABLE pos_payment ADD  CONSTRAINT "pos_payment_employee_id_fkey" FOREIGN KEY ("employee_id") REFERENCES "public"."hr_employee" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  
  """ALTER TABLE pos_session DROP CONSTRAINT "pos_session_employee_id_fkey";""",
  """ALTER TABLE pos_session ADD  CONSTRAINT "pos_session_employee_id_fkey" FOREIGN KEY ("employee_id") REFERENCES "public"."hr_employee" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  
  """ALTER TABLE resource_calendar_attendance DROP CONSTRAINT "resource_calendar_attendance_calendar_id_fkey";""",
  """ALTER TABLE resource_calendar_attendance ADD  CONSTRAINT "resource_calendar_attendance_calendar_id_fkey" FOREIGN KEY ("calendar_id") REFERENCES "public"."resource_calendar" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  
  """ALTER TABLE resource_resource DROP CONSTRAINT "resource_resource_calendar_id_fkey";""",
  """ALTER TABLE resource_resource ADD  CONSTRAINT "resource_resource_calendar_id_fkey" FOREIGN KEY ("calendar_id") REFERENCES "public"."resource_calendar" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",



  """DELETE FROM hr_work_entry""",
  """DELETE FROM hr_attendance""",

  """DELETE FROM ir_model_data WHERE model='hr.employee' AND res_id > 1""",
 
]
for q in queries:
  env.cr.execute(q)

model = "hr.employee"
records = env[model].sudo().search(
    [("active", "in", (True, False))], order="id ASC"
)
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
        name = "employee_%s" % str(r.id).zfill(2)
        
        env["ir.model.data"].create(
            {
                "module": "marin",
                "model": model,
                "name": name,
                "res_id": r.id,
                "noupdate": True,
            }
        )