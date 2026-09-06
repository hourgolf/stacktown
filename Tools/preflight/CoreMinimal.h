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
//
// WHAT IT HAS ACTUALLY MISSED, kept concrete rather than hypothetical so the
// next person can calibrate on evidence instead of on this file's own promises:
//
//   1. Tick()'s sorted iteration. Deleting the sort passes here and always
//      will, because TMap below is std::map, which is ordered. UE's TMap is
//      not, and float addition is not associative, so on the engine that
//      deletion makes Money depend on hash bucketing. Found by reasoning, kept
//      as the declared survivor in mutate.py.
//   2. The game-instance outer. StacktownCityStateTest built its subsystem with
//      NewObject<UStacktownEconomy>(GetTransientPackage()); a
//      UGameInstanceSubsystem needs a UGameInstance as its outer. This harness
//      never constructs a UObject, so it could not have caught it under any
//      mutation. Found by the FIRST real-engine run: build OK, 27/28,
//      Stacktown.CityState.Buy the one red.
//
//   3. A MISSING INCLUDE. StacktownPlacementTest.cpp called CityStateToJson
//      without including StacktownEconomy.h. This harness compiles its whole
//      world into ONE translation unit, so a declaration pulled in by any other
//      header is visible to all of them and no missing include can ever fail
//      here. UBT compiles each .cpp separately and rejected it. Found by the
//      coordinator's build, not by this; fixed in 29150be.
//
//   4. A LOG THAT FAILS A TEST. Stacktown.Handover.MirrorRefusesWhenOwning
//      exercises a refusal that logs at Error - correctly, since two writers is
//      the failure that contract exists to prevent. UE's automation framework
//      fails any test that logs an Error unless the test declares the
//      expectation. This harness has no log capture and no notion of a test
//      failing because of what it printed, so it cannot see that class at all.
//      Found by the coordinator's build (59/60), not by this.
//
// The pattern in all four: this file is blind to anything that is about the
// ENGINE, the BUILD or the TEST FRAMEWORK rather than about the arithmetic. It
// is worth exactly that much.
#pragma once

#include <algorithm>
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
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

	bool StartsWith(const FString& Prefix, int32 /*SearchCase*/ = 0) const
	{
		return S.rfind(Prefix.S, 0) == 0;
	}
	FString TrimStartAndEnd() const
	{
		const char* WS = " \t\n\r\f\v";
		const size_t B = S.find_first_not_of(WS);
		if (B == std::string::npos) { return FString(); }
		const size_t E = S.find_last_not_of(WS);
		return FString(S.substr(B, E - B + 1));
	}

	FString Mid(int32 Start) const
	{
		return Start >= Len() ? FString() : FString(S.substr(static_cast<size_t>(Start)));
	}
	char operator[](int32 i) const { return S[static_cast<size_t>(i)]; }

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

// TMap, backed by a vector so it preserves INSERTION ORDER - which is what UE's
// TMap actually does (coordinator, 2026-09-06), and what an earlier std::map
// here did not. That difference was not academic: keyed order made BOTH sort
// mutations unfalsifiable, because removing an explicit sort still left the
// container sorted. Linear lookup is irrelevant at test sizes and buys back the
// coverage.
template <typename K, typename V>
class TMap
{
public:
	V* Find(const K& Key)
	{
		for (auto& P : Items) { if (P.first == Key) { return &P.second; } }
		return nullptr;
	}
	const V* Find(const K& Key) const
	{
		for (const auto& P : Items) { if (P.first == Key) { return &P.second; } }
		return nullptr;
	}
	V& Add(const K& Key, const V& Value)
	{
		if (V* Existing = Find(Key)) { *Existing = Value; return *Existing; }
		Items.push_back(std::make_pair(Key, Value));
		return Items.back().second;
	}
	bool Contains(const K& Key) const { return Find(Key) != nullptr; }
	int32 Num() const { return static_cast<int32>(Items.size()); }
	V& operator[](const K& Key)
	{
		if (V* Existing = Find(Key)) { return *Existing; }
		return Add(Key, V());
	}
	const V& operator[](const K& Key) const { return *Find(Key); }

	void GetKeys(TArray<K>& Out) const
	{
		for (const auto& P : Items) { Out.Add(P.first); }
	}

	struct FIter
	{
		typename std::vector<std::pair<K, V>>::const_iterator It;
		bool operator!=(const FIter& O) const { return It != O.It; }
		void operator++() { ++It; }
		TPair<K, V> operator*() const { return TPair<K, V>{ It->first, It->second }; }
	};
	FIter begin() const { return FIter{ Items.begin() }; }
	FIter end()   const { return FIter{ Items.end() }; }

	std::vector<std::pair<K, V>> Items;
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
	// std::nearbyint is half-to-even under the default rounding mode, which is
	// what Python's round() does and what the lot-span snap depends on.
	static double RoundHalfToEven(double V) { return std::nearbyint(V); }
	static double Sqrt(double V) { return std::sqrt(V); }
	template <typename T> static T Min(T A, T B) { return A < B ? A : B; }
	template <typename T> static T Max(T A, T B) { return A > B ? A : B; }
};

// ESearchCase exists so the call sites read the same in both worlds; the shim's
// StartsWith is always case-sensitive, which is the only mode the port uses.
struct ESearchCase { enum Type { CaseSensitive = 0, IgnoreCase = 1 }; };

// Only what LotFrame's offsets need; the pose itself is three doubles.
struct FVector
{
	double X = 0.0, Y = 0.0, Z = 0.0;
	FVector() {}
	FVector(double InX, double InY, double InZ) : X(InX), Y(InY), Z(InZ) {}
};

struct FChar { static bool IsDigit(char C) { return C >= '0' && C <= '9'; } };
struct FCString { static int32 Atoi(const char* S) { return std::atoi(S); } };

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

// TOptional, as far as FLotPlacement::RoadId and FParcelState::Placement need
// it. The distinction this type carries is load-bearing here and not cosmetic:
// a lot with NO road_id key is not the same as one whose road_id happens to be
// "arterial", and the owner's real save contains four of the former.
template <typename T>
class TOptional
{
public:
	TOptional() : bSet(false), Value() {}
	TOptional(const T& In) : bSet(true), Value(In) {}
	TOptional& operator=(const T& In) { bSet = true; Value = In; return *this; }
	bool IsSet() const { return bSet; }
	const T& GetValue() const { return Value; }
	T& GetValue() { return Value; }
	void Reset() { bSet = false; Value = T(); }
private:
	bool bSet;
	T Value;
};
