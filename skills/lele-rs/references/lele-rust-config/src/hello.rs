use derive_more::Deref;

#[derive(Debug, Clone, PartialEq, Eq, Deref)]
pub struct Hello(pub String);

impl Hello {
    pub fn new(name: impl Into<String>) -> Self {
        Self(name.into())
    }
}

#[cfg(test)]
mod tests {
    use super::Hello;

    #[test]
    fn test_usage() {
        let h = Hello::new("world");
        assert_eq!(*h, "world");
    }
}
