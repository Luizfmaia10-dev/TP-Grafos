export function maskDepartureTime(value) {
  const separator = value.indexOf(":");
  if (separator >= 0) {
    const hours = value.slice(0, separator).replace(/\D/gu, "");
    const parts = value.slice(separator + 1).split(":");
    const minutes = parts[0].replace(/\D/gu, "");
    if (parts.length > 1 || minutes.length <= 2) {
      return hours ? `${hours}:${minutes.slice(0, 2)}` : minutes.slice(0, 2);
    }
    const digits = hours + minutes;
    return `${digits.slice(0, -2)}:${digits.slice(-2)}`;
  }

  const digits = value.replace(/\D/gu, "");
  if (digits.length <= 2) return digits;
  const hourDigits = digits.length <= 4 ? 2 : digits.length - 2;
  return `${digits.slice(0, hourDigits)}:${digits.slice(hourDigits)}`;
}
