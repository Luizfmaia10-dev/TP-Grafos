export function maskDepartureTime(value) {
  const separator = value.indexOf(":");
  if (separator >= 0) {
    const hours = value.slice(0, separator).replace(/\D/gu, "");
    const minutes = value.slice(separator + 1).split(":", 1)[0].replace(/\D/gu, "").slice(0, 2);
    return hours ? `${hours}:${minutes}` : minutes;
  }

  const digits = value.replace(/\D/gu, "");
  if (digits.length <= 2) return digits;
  const hourDigits = digits.length <= 4 ? 2 : digits.length - 2;
  return `${digits.slice(0, hourDigits)}:${digits.slice(hourDigits)}`;
}
