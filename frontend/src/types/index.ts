/** Response shapes mirroring the Django REST Framework serializers. */

export type Role = "STUDENT" | "ADMIN";

export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
  is_admin: boolean;
  department_name: string | null;
  created_at: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  is_active: boolean;
  /** False until a syllabus has been supplied for the department. */
  has_curriculum: boolean;
  semester_count: number;
  subject_count: number;
}

export interface Semester {
  id: number;
  semester_number: number;
  name: string;
  subject_count: number;
  department: number;
  department_code: string;
  department_name: string;
}

export type CourseType = "THEORY" | "LAB_ORIENTED_THEORY" | "LABORATORY";

/** Course-type vocabulary, kept in one place so no screen invents a label. */
export const COURSE_TYPES: { value: CourseType; label: string; short: string }[] = [
  { value: "THEORY", label: "Theory", short: "THEORY" },
  { value: "LAB_ORIENTED_THEORY", label: "Lab-Oriented Theory", short: "LAB + THEORY" },
  { value: "LABORATORY", label: "Laboratory", short: "LAB" },
];
export type CourseCategory =
  | "HS" | "HSMC" | "HSM" | "MC" | "BS" | "ES" | "PC" | "OE" | "PE";

export interface Subject {
  id: number;
  semester: number;
  semester_number: number;
  semester_name: string;
  department: number;
  department_code: string;
  /** Null for electives the syllabus publishes no code for. Never invented. */
  course_code: string | null;
  course_title: string;
  category: CourseCategory;
  category_label: string;
  course_type: CourseType;
  course_type_label: string;
  l: number;
  t: number;
  p: number;
  credits: number;
  resource_count: number;
  created_at: string;
  updated_at: string;
}

export type ResourceType =
  | "UNIT_1"
  | "UNIT_2"
  | "UNIT_3"
  | "UNIT_4"
  | "UNIT_5"
  | "CAT_1"
  | "CAT_2"
  | "SEMESTER_EXAM";

export interface Resource {
  id: number;
  subject: number;
  subject_code: string | null;
  subject_title: string;
  semester_id: number;
  semester_number: number;
  resource_type: ResourceType;
  resource_type_label: string;
  title: string;
  description: string;
  file_name: string;
  file_type: string;
  file_type_label: string;
  file_ext: string;
  file_size: number;
  inline_viewable: boolean;
  uploaded_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface Stats {
  department: number | null;
  semesters: number;
  subjects: number;
  resources: number;
  exam_resources: number;
  students?: number;
  admins?: number;
  departments?: number;
  uploaded_this_month?: number;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface UserRow {
  id: number;
  name: string;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
  upload_count: number;
}

export type ResourceCounts = Record<ResourceType, number>;

export const RESOURCE_TYPES: ResourceType[] = [
  "UNIT_1",
  "UNIT_2",
  "UNIT_3",
  "UNIT_4",
  "UNIT_5",
  "CAT_1",
  "CAT_2",
  "SEMESTER_EXAM",
];

export const LEARNING_TYPES: ResourceType[] = [
  "UNIT_1",
  "UNIT_2",
  "UNIT_3",
  "UNIT_4",
  "UNIT_5",
];

export const EXAM_TYPES: ResourceType[] = ["CAT_1", "CAT_2", "SEMESTER_EXAM"];

export const RESOURCE_TYPE_LABELS: Record<ResourceType, string> = {
  UNIT_1: "Unit 1",
  UNIT_2: "Unit 2",
  UNIT_3: "Unit 3",
  UNIT_4: "Unit 4",
  UNIT_5: "Unit 5",
  CAT_1: "CAT 1",
  CAT_2: "CAT 2",
  SEMESTER_EXAM: "Semester Exam",
};

export const RESOURCE_TYPE_SLUGS: Record<ResourceType, string> = {
  UNIT_1: "unit-1",
  UNIT_2: "unit-2",
  UNIT_3: "unit-3",
  UNIT_4: "unit-4",
  UNIT_5: "unit-5",
  CAT_1: "cat-1",
  CAT_2: "cat-2",
  SEMESTER_EXAM: "semester-exam",
};

export function resourceTypeFromSlug(slug: string): ResourceType | null {
  const entry = Object.entries(RESOURCE_TYPE_SLUGS).find(([, s]) => s === slug);
  return entry ? (entry[0] as ResourceType) : null;
}

export const CATEGORY_LABELS: Record<CourseCategory, string> = {
  HS: "Humanities & Social Sciences",
  HSMC: "Humanities, Social Sciences & Management",
  HSM: "Humanities & Management",
  MC: "Mandatory Course",
  BS: "Basic Sciences",
  ES: "Engineering Sciences",
  PC: "Professional Core",
  OE: "Open Elective",
  PE: "Professional Elective",
};

export const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];

export function roman(n: number): string {
  return ROMAN[n - 1] ?? String(n);
}
