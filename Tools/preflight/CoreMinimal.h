// A PRE-FLIGHT SHIM, NOT UNREAL. Read this before trusting anything it prints.
//
// The engineering seat runs in a Linux container with no Unreal Engine, so the
// UE Automation tests cannot be built or run from here (Docs/BOARD.md). This
// header is the minimum subset of UE's core types that
// Source/StacktownAlpha/Private/StacktownEconomyRules.cpp actually uses, mapped
// onto the C++ standard library, so that ONE FILE can be compiled and executed
// on a machine without the engine.
//
// WHAT THIS DOES AND DOES NOT PROVE.
//   Proves:  the ported arithmetic, the verb refusals and their exact reason
//            strings, the ordering of the tick, and the ledger's idempotency -
//            executed, against oracle-generated expectations.
//   Does NOT prove: that the real module compiles under UBT, that the Automation
//            tests link or run, or that UE's FString/TMap behave identically to
//            these stand-ins. A shim that passes while the engine fails is
//            exactly the "check asking the wrong question" this project has been
//            bitten by three times (HANDOFF section 5, Measurement).
//
// So: a green harness is a reason to send the branch to the Mac, never a
// substitute for the headless pass line that PLAN_CPP_PORT.md section 3 asks
// for. The pass line is the proof; this is how the port arrives with fewer
// obvious defects still in it.
#pragma once

#include <algorithm>
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <vector>

typedef char     TCHAR;
typedef int32_t  int32;
typedef int64_t  int64;
typedef uint8_t  uint8;

#define TEXT(x) x

class FString
{
public:
	FString() {}
	FString(const char* In) : S(In ? In : "") {}
	FString(const std::string& In) : S(In) {}

	const char* operator*() const { return S.c_str(); }
	bool IsEmpty() const { return S.empty(); }
	int32 Len() const { return static_cast<int32>(S.size()); }

	bool operator==(const FString& O) const { return S == O.S; }
	bool operator!=(const FString& O) const { return S != O.S; }
	bool operator< (const FString& O) const { return S <  O.S; }

	static FString Printf(const char* Fmt, ...)
	{
		char Buf[2048];
		va_list Args;
		va_start(Args, Fmt);
		vsnprintf(Buf, sizeof(Buf), Fmt, Args);
		va_end(Args);
		return FString(Buf);
	}

	std::string S;
};

template <typename K, typename V>
struct TPair
{
	K Key;
	V Value;
};

template <typename T>
class TArray
{
public:
	void Add(const T& V)          { V_.push_back(V); }
	void Reset()                  { V_.clear(); }
	void Reserve(int32 N)         { V_.reserve(static_cast<size_t>(N)); }
	int32 Num() const             { return static_cast<int32>(V_.size()); }
	T& operator[](int32 i)        { return V_[static_cast<size_t>(i)]; }
	const T& operator[](int32 i) const { return V_[static_cast<size_t>(i)]; }

	void Append(const T* Ptr, int32 Count)
	{
		for (int32 i = 0; i < Count; ++i) { V_.push_back(Ptr[i]); }
	}

	template <typename Pred>
	void Sort(Pred P) { std::sort(V_.begin(), V_.end(), P); }
	void Sort()       { std::sort(V_.begin(), V_.end()); }

	typename std::vector<T>::iterator begin() { return V_.begin(); }
	typename std::vector<T>::iterator end()   { return V_.end(); }
	typename std::vector<T>::const_iterator begin() const { return V_.begin(); }
	typename std::vector<T>::const_iterator end()   const { return V_.end(); }

	std::vector<T> V_;
};

template <typename K, typename V>
class TMap
{
public:
	V* Find(const K& Key)
	{
		auto It = M_.find(Key);
		return It == M_.end() ? nullptr : &It->second;
	}
	const V* Find(const K& Key) const
	{
		auto It = M_.find(Key);
		return It == M_.end() ? nullptr : &It->second;
	}
	V& Add(const K& Key, const V& Value) { M_[Key] = Value; return M_[Key]; }
	bool Contains(const K& Key) const    { return M_.find(Key) != M_.end(); }
	int32 Num() const                    { return static_cast<int32>(M_.size()); }
	V& operator[](const K& Key)          { return M_[Key]; }
	const V& operator[](const K& Key) const { return M_.at(Key); }

	void GetKeys(TArray<K>& Out) const
	{
		for (const auto& Pair : M_) { Out.Add(Pair.first); }
	}

	// Range-for yields TPair, matching UE. std::map is ordered and UE's TMap is
	// not - which is precisely why StacktownEconomyRules.cpp sorts explicitly
	// instead of relying on iteration order. This shim must never be the reason
	// that sort looks unnecessary.
	struct FIter
	{
		typename std::map<K, V>::const_iterator It;
		bool operator!=(const FIter& O) const { return It != O.It; }
		void operator++() { ++It; }
		TPair<K, V> operator*() const { return TPair<K, V>{ It->first, It->second }; }
	};
	FIter begin() const { return FIter{ M_.begin() }; }
	FIter end()   const { return FIter{ M_.end() }; }

	std::map<K, V> M_;
};

template <typename T>
class TSet
{
public:
	void Add(const T& V)              { S_.insert(V); }
	bool Contains(const T& V) const   { return S_.find(V) != S_.end(); }
	int32 Num() const                 { return static_cast<int32>(S_.size()); }
	std::set<T> S_;
};

struct FMath
{
	static double Abs(double V) { return V < 0.0 ? -V : V; }
	static double RoundHalfToEven(double V) { return std::nearbyint(V); }
};

// The module export macro is meaningless outside a UE build.
#define STACKTOWNALPHA_API

// Shared pointers, only as far as OracleCatalogue() in the shared test header
// needs them. UE's TSharedRef is non-null by construction; std::shared_ptr is
// not, and nothing here relies on that difference.
#include <memory>
template <typename T> using TSharedPtr = std::shared_ptr<T>;
template <typename T> using TSharedRef = std::shared_ptr<T>;
template <typename T, typename... A> TSharedRef<T> MakeShared(A&&... Args)
{
	return std::make_shared<T>(std::forward<A>(Args)...);
}
